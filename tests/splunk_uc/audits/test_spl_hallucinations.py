"""Unit tests for ``audit-spl-hallucinations`` (P16 wave J).

The SPL-hallucination auditor at
``src/splunk_uc/audits/spl_hallucinations.py`` is the catalogue's
last-line guard against AI-fabricated SPL — typo'd datamodels,
non-existent search commands, malformed tstats, and the "looks
plausible but doesn't exist" field combos that bit UC-5.2.35. It runs
on every PR via ``validate.yml`` and walks the full JSON SSOT under
``content/cat-*/UC-*.json``.

Coverage at the start of this wave: **7.11%** (247 / 276 statements
unexercised).  The tests below pin every documented contract:

* Reference tables (`CIM_DATASETS`, `VALID_COMMANDS`,
  `BAD_COMMAND_PATTERNS`, `KNOWN_HALLUCINATED_FIELDS`) load with the
  shapes the audit assumes.
* The `Finding` dataclass-equivalent with `__slots__` and its
  `__repr__` (snippet truncation included).
* Every pure helper (`strip_comments` removing balanced
  `comment(...)` blocks across single/double quotes and escapes,
  `_mask_tokens` masking dashboard tokens, `split_spl_pipes`
  respecting quotes/brackets/parens/backticks/tokens with embedded
  pipes, `extract_pipe_commands` distinguishing leading-valid from
  leading-unknown commands, `extract_tstats_components` parsing
  every `from/where/by` triple).
* Every check function (`check_in_with_wildcards_in_where_eval`
  fires on `where IN (...*...)` but not on top-level/tstats `IN`,
  `check_tstats` for unknown model + unknown dataset paths,
  `check_bad_patterns` for every entry in `BAD_COMMAND_PATTERNS`,
  `check_known_hallucinated_fields` for every entry in
  `KNOWN_HALLUCINATED_FIELDS`, `check_unknown_commands` distinguishing
  invalid-leading-cmd from invalid-downstream-cmd and ignoring
  comment/backtick segments).
* The `audit_json_file` orchestrator (happy path with no findings,
  malformed JSON path, `spl` + `cimSpl` both audited, missing/empty
  blocks skipped, severity assignment + label-prefixing in the
  message).
* The `main()` CLI (returns 0 when corpus is clean, 1 when any
  finding fires, prints scanned-files + per-category histograms,
  argparse accepts no flags today).
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.audits import spl_hallucinations as sh

# ---------------------------------------------------------------------------
# Harness — write JSON SSOT fixtures under REPO_ROOT/content so audit_json_file
# walks them with stable paths.
# ---------------------------------------------------------------------------


_HARNESS_DIR = Path(sh.REPO_ROOT) / ".pytest-tmp-spl-hallucinations"


def _harness_cat_dir(monkeypatch: pytest.MonkeyPatch) -> Path:
    _teardown_harness()
    _HARNESS_DIR.mkdir(exist_ok=True)
    content_dir = _HARNESS_DIR / "content"
    cat_dir = content_dir / "cat-22-test"
    cat_dir.mkdir(parents=True)
    # Override the constants the audit reads
    monkeypatch.setattr(sh, "CONTENT_DIR", str(content_dir))
    return cat_dir


def _teardown_harness() -> None:
    if _HARNESS_DIR.exists():
        shutil.rmtree(_HARNESS_DIR)


@pytest.fixture(autouse=True)
def _auto_cleanup() -> Iterable[None]:
    yield
    _teardown_harness()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestReferenceTables:
    def test_cim_datasets_known_entries(self) -> None:
        assert "Authentication" in sh.CIM_DATASETS
        assert "Authentication" in sh.CIM_DATASETS["Authentication"]
        assert "All_Traffic" in sh.CIM_DATASETS["Network_Traffic"]
        assert "Web" in sh.CIM_DATASETS["Web"]

    def test_cim_datasets_value_type_is_set(self) -> None:
        for k, v in sh.CIM_DATASETS.items():
            assert isinstance(v, set), f"CIM_DATASETS[{k!r}] is not a set"
            assert len(v) > 0

    def test_valid_commands_contains_core_set(self) -> None:
        for cmd in [
            "stats",
            "table",
            "search",
            "where",
            "eval",
            "rename",
            "tstats",
            "fields",
            "rex",
        ]:
            assert cmd in sh.VALID_COMMANDS

    def test_valid_commands_excludes_unknown(self) -> None:
        assert "frobnicate" not in sh.VALID_COMMANDS

    def test_bad_command_patterns_compiled_regex(self) -> None:
        assert sh.BAD_COMMAND_PATTERNS  # non-empty
        for pat, msg in sh.BAD_COMMAND_PATTERNS:
            assert isinstance(pat, re.Pattern)
            assert isinstance(msg, str) and msg

    def test_known_hallucinated_fields_compiled_regex(self) -> None:
        assert sh.KNOWN_HALLUCINATED_FIELDS
        for pat, msg in sh.KNOWN_HALLUCINATED_FIELDS:
            assert isinstance(pat, re.Pattern)
            assert isinstance(msg, str) and msg


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------


class TestFinding:
    def test_construction_and_attributes(self) -> None:
        f = sh.Finding(
            file="UC-1.1.1.json",
            uc_id="1.1.1",
            severity="HIGH",
            category="parse",
            message="some message",
            snippet="search index=foo",
        )
        assert f.file == "UC-1.1.1.json"
        assert f.uc_id == "1.1.1"
        assert f.severity == "HIGH"
        assert f.category == "parse"
        assert f.message == "some message"
        assert f.snippet == "search index=foo"

    def test_repr_with_snippet(self) -> None:
        f = sh.Finding(
            file="UC-1.1.1.json",
            uc_id="1.1.1",
            severity="HIGH",
            category="parse",
            message="oops",
            snippet="search index=foo",
        )
        out = repr(f)
        assert "[HIGH]" in out
        assert "[parse]" in out
        assert "UC-1.1.1" in out
        assert "oops" in out
        assert "snippet:" in out
        assert "search index=foo" in out

    def test_repr_truncates_long_snippet(self) -> None:
        long_snippet = "search " + "abc " * 200  # well over 120 chars
        f = sh.Finding(
            file="x.json",
            uc_id="9.9.9",
            severity="HIGH",
            category="c",
            message="m",
            snippet=long_snippet,
        )
        out = repr(f)
        # Snippet portion (after "snippet: ") must be <= 120 chars
        snippet_part = out.split("snippet: ", 1)[1]
        assert len(snippet_part) == 120

    def test_repr_without_snippet(self) -> None:
        f = sh.Finding(file="x.json", uc_id="1.1.1", severity="MED", category="c", message="m")
        out = repr(f)
        assert "snippet:" not in out

    def test_uses_slots(self) -> None:
        f = sh.Finding(file="x", uc_id="1.1.1", severity="MED", category="c", message="m")
        # __slots__ prevents arbitrary attribute creation
        with pytest.raises(AttributeError):
            f.unknown_attr = "x"


# ---------------------------------------------------------------------------
# strip_comments
# ---------------------------------------------------------------------------


class TestStripComments:
    def test_removes_balanced_comment_block(self) -> None:
        spl = 'search index=foo comment("this is a note") | stats count'
        out = sh.strip_comments(spl)
        assert "this is a note" not in out
        assert "search index=foo" in out
        assert "stats count" in out

    def test_handles_nested_parens(self) -> None:
        spl = 'search index=foo comment("hello (world)") | head 1'
        out = sh.strip_comments(spl)
        assert "hello" not in out
        assert "head 1" in out

    def test_handles_quoted_paren_inside_comment(self) -> None:
        spl = 'search * comment("token = \\")\\" stays") | stats count'
        out = sh.strip_comments(spl)
        # The comment was correctly closed at the *outer* `)`; the `\")` and
        # `)` inside the quoted string must NOT shift depth
        assert "stays" not in out
        assert "stats count" in out

    def test_handles_single_quotes_inside_comment(self) -> None:
        spl = "search * comment('foo (bar)') | head 1"
        out = sh.strip_comments(spl)
        assert "foo" not in out
        assert "head 1" in out

    def test_no_comment_block_passthrough(self) -> None:
        spl = "search index=foo | stats count"
        assert sh.strip_comments(spl) == spl

    def test_unclosed_comment_does_not_crash(self) -> None:
        spl = 'search index=foo comment("unclosed'
        # Should consume to end of string without raising
        out = sh.strip_comments(spl)
        assert "comment(" not in out

    def test_escape_inside_single_quoted_comment_keeps_balance(self) -> None:
        """Cover the `\\` escape branch inside single-quoted comment string."""

        spl = "search * comment('foo\\'bar(baz)') | head 1"
        out = sh.strip_comments(spl)
        # The escaped `\'` keeps us inside the single-quoted string until the
        # real closing quote; the parentheses inside stay balanced
        assert "foo" not in out
        assert "head 1" in out

    def test_nested_parens_outside_quotes_consume_correctly(self) -> None:
        """Cover the (`(`/`)`) depth-tracking branch with nested parens."""

        spl = "search * comment(extra (nested) parens) | stats count"
        out = sh.strip_comments(spl)
        assert "nested" not in out
        assert "stats count" in out


# ---------------------------------------------------------------------------
# _mask_tokens
# ---------------------------------------------------------------------------


class TestMaskTokens:
    def test_masks_dashboard_token(self) -> None:
        spl = "search index=foo earliest=$earliest$ latest=$latest$"
        out = sh._mask_tokens(spl)
        assert "$earliest$" not in out
        assert "$latest$" not in out
        assert "XXXXXXXXXX" in out  # X-padded to original length

    def test_masks_token_with_filter_suffix(self) -> None:
        spl = "search index=$host|s$"
        out = sh._mask_tokens(spl)
        assert "$host|s$" not in out

    def test_no_token_passthrough(self) -> None:
        spl = "search * | stats count"
        assert sh._mask_tokens(spl) == spl


# ---------------------------------------------------------------------------
# split_spl_pipes
# ---------------------------------------------------------------------------


class TestSplitSplPipes:
    def test_simple_pipeline(self) -> None:
        segs = sh.split_spl_pipes("search * | stats count | sort - count")
        assert segs == ["search *", "stats count", "sort - count"]

    def test_ignores_pipes_inside_double_quotes(self) -> None:
        segs = sh.split_spl_pipes('search index=foo bar="a|b|c" | stats count')
        assert segs == ['search index=foo bar="a|b|c"', "stats count"]

    def test_ignores_pipes_inside_single_quotes(self) -> None:
        segs = sh.split_spl_pipes("search foo='a|b' | head 1")
        assert segs == ["search foo='a|b'", "head 1"]

    def test_ignores_pipes_inside_backticks(self) -> None:
        segs = sh.split_spl_pipes("`mymacro(a|b)` | stats count")
        assert len(segs) == 2

    def test_ignores_pipes_inside_parens(self) -> None:
        segs = sh.split_spl_pipes("search | eval x=if(a|b, 1, 0) | stats count")
        # The if() contains an unsplit pipe; depth tracking keeps it together
        # The single bare pipe in `if(a|b, ...)` is inside paren depth 1 → no split
        assert any("if(a|b" in s for s in segs)

    def test_ignores_pipes_inside_brackets(self) -> None:
        # Subsearch
        segs = sh.split_spl_pipes("search [search index=foo | stats count]")
        assert len(segs) == 1

    def test_handles_escaped_quote_inside_string(self) -> None:
        segs = sh.split_spl_pipes('search foo="a\\"|b" | head 1')
        # Escape skips the embedded quote; pipe-inside-quote not a separator
        assert len(segs) == 2

    def test_handles_escaped_quote_inside_single_quotes(self) -> None:
        """Cover the `in_sq` escape branch (lines 593-596)."""

        segs = sh.split_spl_pipes("search foo='a\\'|b' | head 1")
        # The escape inside single quotes prevents the embedded `'` from
        # closing the string, so the embedded pipe is still inside quotes
        assert len(segs) == 2

    def test_strips_segments(self) -> None:
        segs = sh.split_spl_pipes("  search *  |  stats count  ")
        assert segs == ["search *", "stats count"]

    def test_masks_dashboard_tokens_before_split(self) -> None:
        # Dashboard token containing pipe-like char should not be split
        segs = sh.split_spl_pipes("search index=$host|s$ | stats count")
        assert len(segs) == 2

    def test_empty_string(self) -> None:
        assert sh.split_spl_pipes("") == []

    def test_drops_empty_trailing_segment(self) -> None:
        segs = sh.split_spl_pipes("search * | ")
        assert segs == ["search *"]


# ---------------------------------------------------------------------------
# extract_pipe_commands
# ---------------------------------------------------------------------------


class TestExtractPipeCommands:
    def test_records_known_leading_command(self) -> None:
        cmds = sh.extract_pipe_commands("search * | stats count")
        assert cmds == ["search", "stats"]

    def test_skips_unknown_leading_command(self) -> None:
        """The leading segment is treated as the implicit search; only
        records it if it matches a known command."""
        cmds = sh.extract_pipe_commands("index=foo | stats count")
        # "index=foo" — first word "index" is not a command → skipped
        assert cmds == ["stats"]

    def test_records_unknown_downstream_command(self) -> None:
        cmds = sh.extract_pipe_commands("search * | frobnicate")
        assert "frobnicate" in cmds

    def test_skips_comment_segments(self) -> None:
        cmds = sh.extract_pipe_commands('search * | comment("note") | stats count')
        # comment( does *not* contribute a command
        assert "comment" not in cmds
        assert "stats" in cmds

    def test_skips_backtick_macro_segments(self) -> None:
        cmds = sh.extract_pipe_commands("search * | `mymacro` | stats count")
        # backtick segments are skipped
        assert "mymacro" not in cmds
        assert "stats" in cmds

    def test_handles_empty_segments(self) -> None:
        # `split_spl_pipes` strips empties, so the test is around index=0
        # being non-command
        assert sh.extract_pipe_commands("") == []

    def test_skips_segment_without_token_match(self) -> None:
        """Covers line 670 — when `tok` is None (segment starts with a
        non-identifier char like `(`)."""

        cmds = sh.extract_pipe_commands("search * | ( some subexpr )")
        # Leading `search` recorded; the `(...)` segment has no command word
        # so the `if tok:` is False
        assert cmds == ["search"]

    def test_defensive_empty_segment_guard_covered_via_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Covers line 659 (`if not s: continue`) — the defensive guard
        against empty pipe segments.

        ``split_spl_pipes`` already strips empties (`if s.strip()`), so in
        normal use this branch is unreachable. We pin the guard explicitly
        by injecting an empty segment via ``split_spl_pipes`` so a future
        refactor of the strip logic can't silently break this contract.
        """

        def _fake_split_with_empty(_spl: str) -> list[str]:
            return ["", "stats count"]

        monkeypatch.setattr(sh, "split_spl_pipes", _fake_split_with_empty)
        cmds = sh.extract_pipe_commands("ignored — split is mocked")
        assert cmds == ["stats"]


# ---------------------------------------------------------------------------
# extract_tstats_components
# ---------------------------------------------------------------------------


class TestExtractTstatsComponents:
    def test_full_triple_parsed(self) -> None:
        spl = "tstats summariesonly=t count from datamodel=Authentication.Authentication where action=success by user"
        out = sh.extract_tstats_components(spl)
        assert len(out) == 1
        d = out[0]
        assert d["model"] == "Authentication"
        assert d["dataset"] == "Authentication"
        assert "action=success" in d["where"]
        assert "user" in d["by"]

    def test_model_only_no_dataset(self) -> None:
        spl = "tstats count from datamodel=Network_Traffic by sourcetype"
        out = sh.extract_tstats_components(spl)
        assert out[0]["model"] == "Network_Traffic"
        assert out[0].get("dataset", "") == ""

    def test_no_tstats_returns_empty_list(self) -> None:
        assert sh.extract_tstats_components("search * | stats count") == []

    def test_tstats_without_from_clause(self) -> None:
        """Covers the 501→504 branch — `fm` is None when there's no
        `from datamodel=...`."""

        # `tstats count where x=1` has no `from datamodel=...` → no model/dataset
        out = sh.extract_tstats_components("tstats count where x=1 by y")
        assert len(out) == 1
        assert out[0].get("model", "") == ""
        assert "x=1" in out[0]["where"]

    def test_multiple_tstats_each_parsed(self) -> None:
        spl = (
            "tstats count from datamodel=Authentication by user | "
            "tstats count from datamodel=Web.Web by src"
        )
        out = sh.extract_tstats_components(spl)
        assert len(out) == 2
        assert out[0]["model"] == "Authentication"
        assert out[1]["model"] == "Web"
        assert out[1]["dataset"] == "Web"


# ---------------------------------------------------------------------------
# check_in_with_wildcards_in_where_eval
# ---------------------------------------------------------------------------


class TestCheckInWithWildcardsInWhereEval:
    def test_fires_on_where_with_wildcard_in(self) -> None:
        spl = 'search * | where action IN ("login*", "logout")'
        findings = sh.check_in_with_wildcards_in_where_eval(spl)
        assert findings
        assert findings[0][0] == "in_wildcard_where_eval"

    def test_fires_on_eval_with_wildcard_in(self) -> None:
        spl = 'search * | eval x=IN(action, "*err*")'
        findings = sh.check_in_with_wildcards_in_where_eval(spl)
        assert findings

    def test_silent_for_search_in_clause(self) -> None:
        # IN(...) in main search command is supported
        spl = 'search action IN ("login*", "logout")'
        assert sh.check_in_with_wildcards_in_where_eval(spl) == []

    def test_silent_when_no_wildcards(self) -> None:
        spl = 'search * | where action IN ("login", "logout")'
        assert sh.check_in_with_wildcards_in_where_eval(spl) == []


# ---------------------------------------------------------------------------
# check_tstats
# ---------------------------------------------------------------------------


class TestCheckTstats:
    def test_unknown_model(self) -> None:
        spl = "tstats count from datamodel=MadeUp by user"
        findings = sh.check_tstats(spl)
        assert findings
        assert findings[0][0] == "cim_model_unknown"
        assert "MadeUp" in findings[0][1]

    def test_unknown_dataset_in_known_model(self) -> None:
        spl = "tstats count from datamodel=Authentication.MadeUpDataset by user"
        findings = sh.check_tstats(spl)
        assert findings
        assert findings[0][0] == "cim_dataset_unknown"
        assert "MadeUpDataset" in findings[0][1]

    def test_known_model_and_dataset_silent(self) -> None:
        spl = "tstats count from datamodel=Authentication.Authentication by user"
        assert sh.check_tstats(spl) == []

    def test_no_tstats_silent(self) -> None:
        assert sh.check_tstats("search * | stats count") == []


# ---------------------------------------------------------------------------
# check_bad_patterns
# ---------------------------------------------------------------------------


class TestCheckBadPatterns:
    def test_performace_typo(self) -> None:
        findings = sh.check_bad_patterns("tstats count from datamodel=Performace by host")
        assert findings
        assert findings[0][0] == "pattern"
        assert "Performance" in findings[0][1]

    def test_authenthication_typo(self) -> None:
        findings = sh.check_bad_patterns("tstats count from datamodel=Authenthication by user")
        assert findings and "Authentication" in findings[0][1]

    def test_netowrk_typo(self) -> None:
        findings = sh.check_bad_patterns("tstats count from datamodel=Netowrk_Traffic by src")
        assert findings and "Network_Traffic" in findings[0][1]

    def test_networ_typo(self) -> None:
        findings = sh.check_bad_patterns("tstats count from datamodel=Networ_Traffic by src")
        assert findings

    def test_change_analysis_legacy(self) -> None:
        findings = sh.check_bad_patterns("tstats count from datamodel=Change_Analysis by user")
        assert findings and "Change_Analysis" in findings[0][1]

    def test_summariesonly_true_lowercase(self) -> None:
        findings = sh.check_bad_patterns("tstats summariesonly=true count from datamodel=Web")
        assert findings and "summariesonly=t" in findings[0][1]

    def test_summariesonly_false_uppercase(self) -> None:
        findings = sh.check_bad_patterns("tstats SUMMARIESONLY=FALSE count from datamodel=Web")
        assert findings

    def test_clean_spl_silent(self) -> None:
        assert sh.check_bad_patterns("tstats summariesonly=t count from datamodel=Web") == []


# ---------------------------------------------------------------------------
# check_known_hallucinated_fields
# ---------------------------------------------------------------------------


class TestCheckKnownHallucinatedFields:
    def test_cisco_network_meraki_combo(self) -> None:
        spl = 'search index=cisco_network sourcetype="meraki" | stats count'
        findings = sh.check_known_hallucinated_fields(spl)
        assert findings
        assert findings[0][0] == "hallucinated_field"

    def test_meraki_security_event(self) -> None:
        spl = "search sourcetype=meraki type=security_event | stats count"
        findings = sh.check_known_hallucinated_fields(spl)
        assert any("security_event" in m for _c, m in findings)

    def test_meraki_signature_cellular(self) -> None:
        spl = 'search sourcetype=meraki signature="*Cellular*" | stats count'
        findings = sh.check_known_hallucinated_fields(spl)
        assert findings

    def test_meraki_data_usage_mb(self) -> None:
        spl = "search sourcetype=meraki_events data_usage_mb=*"
        findings = sh.check_known_hallucinated_fields(spl)
        assert any("data_usage_mb" in m for _c, m in findings)

    def test_meraki_event_type_connection_error(self) -> None:
        spl = 'search sourcetype=meraki event_type="connection_error"'
        findings = sh.check_known_hallucinated_fields(spl)
        assert findings

    def test_clean_silent(self) -> None:
        assert sh.check_known_hallucinated_fields("search sourcetype=meraki type=flows") == []


# ---------------------------------------------------------------------------
# check_unknown_commands
# ---------------------------------------------------------------------------


class TestCheckUnknownCommands:
    def test_unknown_command_flagged(self) -> None:
        findings = sh.check_unknown_commands("search * | frobnicate")
        assert findings
        assert findings[0][0] == "unknown_command"
        assert "frobnicate" in findings[0][1]

    def test_known_commands_silent(self) -> None:
        findings = sh.check_unknown_commands("search * | stats count | sort - count")
        assert findings == []

    def test_unknown_leading_command_silent(self) -> None:
        """The leading segment is treated as the implicit search and unknown
        leading words are skipped by ``extract_pipe_commands``."""
        findings = sh.check_unknown_commands("index=foo | stats count")
        assert findings == []


# ---------------------------------------------------------------------------
# audit_json_file
# ---------------------------------------------------------------------------


def _write_uc(cat_dir: Path, uc_id: str, doc: dict[str, Any]) -> Path:
    p = cat_dir / f"UC-{uc_id}.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


class TestAuditJsonFile:
    def test_no_spl_no_findings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(cat_dir, "1.1.1", {"id": "1.1.1", "spl": ""})
        findings = sh.audit_json_file(str(p))
        assert findings == []

    def test_clean_spl_no_findings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {"id": "1.1.1", "spl": "search index=foo | stats count by host"},
        )
        assert sh.audit_json_file(str(p)) == []

    def test_unknown_command_fires(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {"id": "1.1.1", "spl": "search index=foo | frobnicate"},
        )
        findings = sh.audit_json_file(str(p))
        assert any(f.category == "unknown_command" for f in findings)
        assert all(f.severity == "HIGH" for f in findings if f.category == "unknown_command")
        # Label-prefixed message
        assert any("[SPL]" in f.message for f in findings)

    def test_tstats_unknown_model_fires(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {
                "id": "1.1.1",
                "spl": "tstats count from datamodel=Imaginary by user",
            },
        )
        findings = sh.audit_json_file(str(p))
        assert any(f.category == "cim_model_unknown" for f in findings)

    def test_bad_pattern_fires_med_severity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {
                "id": "1.1.1",
                "spl": "tstats summariesonly=true count from datamodel=Web",
            },
        )
        findings = sh.audit_json_file(str(p))
        bad = [f for f in findings if f.category == "pattern"]
        assert bad
        assert bad[0].severity == "MED"

    def test_in_wildcard_in_where_fires_med(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {
                "id": "1.1.1",
                "spl": 'search * | where action IN ("login*")',
            },
        )
        findings = sh.audit_json_file(str(p))
        ivf = [f for f in findings if f.category == "in_wildcard_where_eval"]
        assert ivf and ivf[0].severity == "MED"

    def test_hallucinated_field_fires_high(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {
                "id": "1.1.1",
                "spl": "search sourcetype=meraki type=security_event",
            },
        )
        findings = sh.audit_json_file(str(p))
        h = [f for f in findings if f.category == "hallucinated_field"]
        assert h and h[0].severity == "HIGH"

    def test_cimspl_block_also_audited(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {
                "id": "1.1.1",
                "spl": "search index=foo | stats count",
                "cimSpl": "tstats count from datamodel=ImaginaryModel by user",
            },
        )
        findings = sh.audit_json_file(str(p))
        labels = {"SPL" if "[SPL]" in f.message else "CIMSPL" for f in findings}
        # Only CIM SPL has a finding (the ImaginaryModel)
        cim_findings = [f for f in findings if "[CIM SPL]" in f.message]
        assert cim_findings
        assert "CIMSPL" in labels

    def test_malformed_json_emits_parse_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = cat_dir / "UC-bad.json"
        p.write_text("{ this is not json", encoding="utf-8")
        findings = sh.audit_json_file(str(p))
        assert len(findings) == 1
        assert findings[0].category == "parse"
        assert findings[0].severity == "ERROR"

    def test_uses_filename_when_id_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "9.9.9",
            {"spl": "search * | frobnicate"},  # no id
        )
        findings = sh.audit_json_file(str(p))
        # uc_id falls back to the JSON filename
        assert any(f.uc_id == "UC-9.9.9.json" for f in findings)

    def test_first_line_used_as_snippet(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        p = _write_uc(
            cat_dir,
            "1.1.1",
            {"id": "1.1.1", "spl": "search index=foo\n| frobnicate"},
        )
        findings = sh.audit_json_file(str(p))
        f = next(f for f in findings if f.category == "unknown_command")
        assert f.snippet == "search index=foo"


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    def test_clean_corpus_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        _write_uc(cat_dir, "1.1.1", {"id": "1.1.1", "spl": "search * | stats count"})
        rc = sh.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Scanned 1 JSON SSOT files" in out
        assert "Total findings: 0" in out

    def test_dirty_corpus_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        _write_uc(cat_dir, "1.1.1", {"id": "1.1.1", "spl": "search * | frobnicate"})
        rc = sh.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "Total findings:" in out
        assert "unknown_command" in out

    def test_empty_corpus_returns_zero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _harness_cat_dir(monkeypatch)
        rc = sh.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Scanned 0 JSON SSOT files" in out

    def test_per_category_breakdown_printed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cat_dir = _harness_cat_dir(monkeypatch)
        _write_uc(
            cat_dir,
            "1.1.1",
            {"id": "1.1.1", "spl": "search * | frobnicate | wibble"},
        )
        sh.main([])
        out = capsys.readouterr().out
        # Both per-category line and the verbose `=== {cat} (N) ===` section
        assert "unknown_command" in out
        assert "=== unknown_command" in out

    def test_argparse_accepts_no_flags(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _harness_cat_dir(monkeypatch)
        # argparse with no args defined should accept argv=[] cleanly
        rc = sh.main([])
        assert rc == 0
