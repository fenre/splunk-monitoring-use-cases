"""Unit tests for the SPL reference parser + audit.

These tests pin the externally-observable contracts of:

* ``splunk_uc.audits._spl_parse`` — extraction primitives shared
  by every reference-validating audit.
* ``splunk_uc.audits.spl_references`` — the new ``audit-spl-references``
  verb. Only the audit harness shape is tested here; the catalog-wide
  sweep happens in CI via the dispatcher entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Parser primitives
# ---------------------------------------------------------------------------


def test_extract_macros_simple() -> None:
    from splunk_uc.audits._spl_parse import extract_macros

    spl = "`security_content_summariesonly` index=foo `myMacro(1, 2)`"
    refs = extract_macros(spl)
    names = [r.name for r in refs]
    assert "security_content_summariesonly" in names
    assert "myMacro" in names
    arities = {r.name: r.arity for r in refs}
    assert arities["security_content_summariesonly"] == -1  # no parens
    assert arities["myMacro"] == 2


def test_extract_macros_dotted_name() -> None:
    """Authoring bug: backtick-wrapped JSON field path becomes a phantom macro."""
    from splunk_uc.audits._spl_parse import extract_macros

    spl = "| eval x=coalesce(involvedObject.kind, `involvedObject.kind`, \"\")"
    refs = extract_macros(spl)
    assert any(r.name == "involvedObject.kind" for r in refs)


def test_extract_sourcetypes_basic() -> None:
    from splunk_uc.audits._spl_parse import extract_sourcetypes

    spl = 'index=main sourcetype="aws:cloudtrail" earliest=-1h'
    refs = extract_sourcetypes(spl)
    assert len(refs) == 1
    assert refs[0].value == "aws:cloudtrail"
    assert refs[0].is_wildcard is False


def test_extract_sourcetypes_ignores_double_equals() -> None:
    """sourcetype== inside a case() / eval is COMPARISON, not predicate."""
    from splunk_uc.audits._spl_parse import extract_sourcetypes

    spl = (
        '| eval vendor=case(sourcetype=="aws:cloudtrail", "aws-s3", '
        'sourcetype=="azure:storage:diagnostic", "azure")'
    )
    refs = extract_sourcetypes(spl)
    assert refs == [], f"unexpected predicate match: {refs!r}"


def test_extract_indexes_ignores_double_equals() -> None:
    from splunk_uc.audits._spl_parse import extract_indexes

    spl = '| eval origin=case(index=="hot", "hot-tier")'
    assert extract_indexes(spl) == []


def test_extract_datamodel_path_uppercase_only() -> None:
    """Datamodel model names always start with uppercase; the regex should
    refuse to match `datamodel=if(...)` (eval expression assigning to a
    field literally named `datamodel`).
    """
    from splunk_uc.audits._spl_parse import extract_datamodel_paths

    spl = "| tstats count FROM datamodel=Authentication.Successful_Authentication BY src"
    refs = extract_datamodel_paths(spl)
    assert len(refs) == 1
    assert refs[0].model == "Authentication"
    assert refs[0].dataset == "Successful_Authentication"

    # ``datamodel=if(...)`` must NOT match (case is wrong).
    refs = extract_datamodel_paths('eval datamodel=if(x>0, "yes", "no")')
    assert refs == []


def test_extract_commands_implicit_search_predicate_skipped() -> None:
    """`source="..."` is an implicit-search field predicate, not a command."""
    from splunk_uc.audits._spl_parse import extract_commands

    spl = 'source="WinEventLog:Security" EventCode=4624 host=*'
    cmds = extract_commands(spl)
    # We don't include 'source' as a command because the lookahead saw `=`.
    assert "source" not in cmds


def test_split_pipes_handles_escaped_quotes() -> None:
    """Pipe splitter must NOT close a double-quoted string at ``\\"``.

    Without the fix, the embedded regex ``|`` characters surface as
    pipe boundaries; with the fix they're protected as part of the
    string literal.
    """
    from splunk_uc.audits._spl_parse import split_pipes

    spl = 'rex field=_raw "(?i)(a|b|c)[=:\\"\\s]+(?<x>\\w+)" | eval y=1'
    segs = [s for s in split_pipes(spl) if s.strip()]
    assert len(segs) == 2, f"unexpected segments: {segs}"
    assert segs[0].startswith("rex field=_raw")
    assert segs[1].startswith("eval y=1")


def test_extract_lookups_basic() -> None:
    """``lookup``/``inputlookup``/``outputlookup`` references are extracted."""
    from splunk_uc.audits._spl_parse import extract_lookups

    spl = (
        "| inputlookup asset_inventory.csv\n"
        "| search status=active\n"
        "| lookup user_lookup user OUTPUT department\n"
        "| outputlookup append=true known_good.csv\n"
    )
    refs = extract_lookups(spl)
    cmds = [r.command for r in refs]
    names = [r.name for r in refs]
    assert "inputlookup" in cmds and "asset_inventory.csv" in names
    assert "lookup" in cmds and "user_lookup" in names
    assert "outputlookup" in cmds and "known_good.csv" in names


def test_extract_stats_function_rejects_whitespace_before_paren() -> None:
    """``Application_State (predicate)`` is NOT ``Application_State(...)``.

    Splunk function calls are always tight (no whitespace between the
    identifier and the open paren). The audit-spl-references parser
    must reject the loose form so we don't false-positive on tstats
    syntax like ``WHERE nodename=Application_State (subpredicate)``.
    """
    from splunk_uc.audits._spl_parse import extract_stats_functions

    spl = (
        '| tstats count(Application_State.process_name) FROM datamodel=Application_State '
        'WHERE nodename=Application_State (Application_State.app="docker") '
        "BY Application_State.dest"
    )
    fns = {f.name for f in extract_stats_functions(spl)}
    assert "application_state" not in fns, (
        f"loose-paren false positive returned: {fns!r}"
    )
    assert "count" in fns, f"tight `count(` should be picked up: {fns!r}"


# ---------------------------------------------------------------------------
# Audit harness
# ---------------------------------------------------------------------------


def test_audit_returns_zero_high_findings_on_synthetic_clean_spl(tmp_path: Path) -> None:
    """A spotless SPL string must produce zero HIGH findings."""
    from splunk_uc.audits.spl_references import (
        Vocabulary,
        build_vocabulary,
        check_one_spl_field,
    )

    vocab = build_vocabulary()
    spl = (
        '`comment("UC clean")`\n'
        '| tstats summariesonly=t count FROM datamodel=Authentication '
        "BY Authentication.src\n"
        '| rename Authentication.src AS src\n'
        '| eval auth_count=if(count > 100, "high", "low")\n'
    )
    findings = check_one_spl_field(
        uc_id="0.0.0",
        file_label="test.json",
        field="spl",
        spl=spl,
        vocab=vocab,
        declared_sourcetypes=set(),
        declared_indexes=set(),
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert high == [], f"unexpected HIGH: {high}"


def test_audit_flags_unknown_command() -> None:
    from splunk_uc.audits.spl_references import (
        build_vocabulary,
        check_one_spl_field,
    )

    vocab = build_vocabulary()
    spl = "| frobnicate index=main"
    findings = check_one_spl_field(
        uc_id="0.0.0",
        file_label="test.json",
        field="spl",
        spl=spl,
        vocab=vocab,
        declared_sourcetypes=set(),
        declared_indexes=set(),
    )
    cats = [f.category for f in findings if f.severity == "HIGH"]
    assert "unknown-command" in cats


def test_audit_flags_unknown_datamodel() -> None:
    from splunk_uc.audits.spl_references import (
        build_vocabulary,
        check_one_spl_field,
    )

    vocab = build_vocabulary()
    spl = "| tstats count FROM datamodel=NotARealModel.NotARealDataset BY src"
    findings = check_one_spl_field(
        uc_id="0.0.0",
        file_label="test.json",
        field="spl",
        spl=spl,
        vocab=vocab,
        declared_sourcetypes=set(),
        declared_indexes=set(),
    )
    cats = {f.category for f in findings}
    assert "unknown-datamodel" in cats


def test_audit_tolerates_escu_filter_macro_suffix() -> None:
    """ESCU's ``<detection_name>_filter`` convention is auto-tolerated."""
    from splunk_uc.audits.spl_references import (
        build_vocabulary,
        check_one_spl_field,
    )

    vocab = build_vocabulary()
    spl = (
        "`comment(\"detection\")`\n"
        "| search index=main\n"
        "| `detect_aws_console_login_by_new_user_filter`\n"
    )
    findings = check_one_spl_field(
        uc_id="0.0.0",
        file_label="test.json",
        field="spl",
        spl=spl,
        vocab=vocab,
        declared_sourcetypes=set(),
        declared_indexes=set(),
    )
    macro_findings = [f for f in findings if f.category == "unknown-macro"]
    assert macro_findings == [], (
        f"_filter macro convention should be tolerated; got: {macro_findings!r}"
    )


def test_audit_dispatcher_help_contains_new_verb() -> None:
    """The new audit-spl-references verb must appear in the dispatcher's --help."""
    from splunk_uc._registry import all_verbs

    names = {v.name for v in all_verbs()}
    assert "audit-spl-references" in names


def test_audit_module_imports_cleanly() -> None:
    """The audit must import without side effects (idempotency under reload)."""
    import importlib

    importlib.import_module("splunk_uc.audits.spl_references")
    importlib.import_module("splunk_uc.audits._spl_parse")
    importlib.import_module("splunk_uc.audits._spl_baseline")
    importlib.import_module("splunk_uc.audits._spl_well_known")


@pytest.mark.parametrize(
    "name,expect",
    [
        ("perc95", True),
        ("perc99", True),
        ("upperperc95", True),
        ("exactperc99", True),
        ("p50", True),
        ("p99", True),
        ("perc", False),  # bare prefix without digits is the alias name itself
        ("p", False),  # bare 'p' is not a percentile function name
        ("count", False),
        ("perc1d", False),
    ],
)
def test_is_perc_function(name: str, expect: bool) -> None:
    from splunk_uc.audits._spl_baseline import is_perc_function

    assert is_perc_function(name) is expect


def test_baseline_does_not_list_perc_or_p_as_full_function_names() -> None:
    """Regression: ``perc`` / ``p`` are prefixes (handled by ``is_perc_function``).

    Listing them in ``VALID_STATS_FUNCTIONS`` would let a literal call like
    ``perc(field)`` pass the audit even though no such Splunk function exists.
    The percentile family is parametric in the function name itself
    (``perc<n>`` / ``p<n>`` / ``upperperc<n>`` / ``exactperc<n>``).
    """
    from splunk_uc.audits._spl_baseline import VALID_STATS_FUNCTIONS

    assert "perc" not in VALID_STATS_FUNCTIONS
    assert "p" not in VALID_STATS_FUNCTIONS


def test_audit_main_check_mode_returns_zero_when_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    """``audit-spl-references --check`` returns 0 when no HIGH findings exist."""
    from splunk_uc.audits import spl_references as mod

    monkeypatch.setattr(mod, "run_audit", lambda **kw: [])  # noqa: ARG005
    rc = mod.main(["--check"])
    assert rc == 0


def test_audit_main_check_mode_returns_one_on_high(monkeypatch: pytest.MonkeyPatch) -> None:
    """``audit-spl-references --check`` returns 1 when ANY HIGH finding exists."""
    from splunk_uc.audits import spl_references as mod

    fake = mod.Finding(
        file="x.json",
        uc_id="0.0.0",
        severity="HIGH",
        category="unknown-command",
        field="spl",
        identifier="frobnicate",
        message="unknown SPL command `frobnicate`",
    )
    monkeypatch.setattr(mod, "run_audit", lambda **kw: [fake])  # noqa: ARG005
    rc = mod.main(["--check", "--summary-only"])
    assert rc == 1


def test_audit_main_json_output_contains_summary_and_vocabulary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``audit-spl-references --json`` emits a summary + vocabulary block."""
    import json as _json

    from splunk_uc.audits import spl_references as mod

    monkeypatch.setattr(mod, "run_audit", lambda **kw: [])  # noqa: ARG005
    rc = mod.main(["--json"])
    assert rc == 0
    captured = capsys.readouterr()
    payload = _json.loads(captured.out)
    assert "summary" in payload
    assert "vocabulary" in payload
    assert payload["vocabulary"]["commands"] >= 100, payload["vocabulary"]
    assert payload["vocabulary"]["datamodel_paths"] >= 100, payload["vocabulary"]
    assert payload["summary"]["by_severity"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}


# ---------------------------------------------------------------------------
# Splunk 9+ ``IN (...)`` predicate: must not be flagged as command ``index``
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spl,expected",
    [
        # ``index IN (...)`` is the Splunk 9+ membership predicate.
        ('index IN ("a","b","c")\n| stats count', ["stats"]),
        # Multi-clause variant.
        ('index IN ("a") OR index IN ("b") | stats count', ["stats"]),
        # ``NOT`` is an operator, not a command — strip it before matching.
        ('NOT index IN ("a","b") | stats count', ["stats"]),
        ('NOT sourcetype="aws:cloudtrail" | stats count', ["stats"]),
        # ``OR`` / ``AND`` as leading tokens of an implicit clause.
        ("OR foo=bar AND baz=qux | stats count", ["stats"]),
        # Lower-case ``in`` with a list — same predicate.
        ("status in (200, 302) | stats count", ["stats"]),
        # Sanity: the literal ``index`` SPL command (rare but legal at
        # the start of a piped clause) must still surface.
        ("| index foo bar", ["index"]),
    ],
    ids=[
        "index_in_list",
        "index_in_or_index_in",
        "not_index_in",
        "not_sourcetype_eq",
        "leading_or_and",
        "lowercase_in",
        "literal_index_command",
    ],
)
def test_extract_commands_skips_in_list_predicates(spl: str, expected: list[str]) -> None:
    """Regression: Splunk 9 ``index IN (...)`` is a predicate, not the ``index`` command.

    The previous parser surfaced ``index`` as an unknown SPL command
    (HIGH severity finding) for every UC that used the modern membership
    syntax. The fix in ``extract_commands`` must skip ``IN (...)``
    predicates and step over leading boolean operators (NOT/OR/AND) the
    same way it steps over ``=`` predicates.
    """
    from splunk_uc.audits._spl_parse import extract_commands

    assert extract_commands(spl) == expected


# ---------------------------------------------------------------------------
# Sourcetype glob matching: corpus-shipped wildcards (``cisco:ise:*``)
# must resolve concrete sourcetypes the catalogue cites.
# ---------------------------------------------------------------------------


def _make_vocab_for_glob_test():
    """Build a Vocabulary with a small, representative glob corpus."""
    from splunk_uc.audits.spl_references import Vocabulary

    return Vocabulary(
        commands=set(),
        macros=set(),
        sourcetypes={"aws:cloudtrail"},
        sourcetype_glob_patterns={
            "cisco:ise:*",  # trailing-wildcard family
            "*365:cas:api",  # leading-wildcard family
            "vmware:*:syslog",  # mid-wildcard family
        },
        indexes=set(),
        datamodel_paths=set(),
        lookups=set(),
        eval_functions=set(),
        stats_functions=set(),
        cim_models=set(),
        sources=[],
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("aws:cloudtrail", True),  # literal hit
        ("cisco:ise:auth", True),  # cisco:ise:* glob
        ("cisco:ise:profiler", True),  # cisco:ise:* glob
        ("o365:cas:api", True),  # *365:cas:api glob
        ("M365:cas:api", True),  # *365:cas:api glob, case-respecting
        ("vmware:nsxt:syslog", True),  # vmware:*:syslog glob
        ("vmware:vsan:syslog", True),  # vmware:*:syslog glob
        ("not_a_real_sourcetype", False),  # truly unknown
        ("aws:cloudwatch", False),  # close but not declared
        ("cisco:foo", False),  # right vendor, wrong family
    ],
)
def test_vocabulary_matches_sourcetype(value: str, expected: bool) -> None:
    """Both literal and glob membership are honoured by ``matches_sourcetype``."""
    vocab = _make_vocab_for_glob_test()
    assert vocab.matches_sourcetype(value) is expected


def test_vocabulary_glob_regex_compiled_once() -> None:
    """The compiled regex is cached so per-UC checks stay O(1)."""
    vocab = _make_vocab_for_glob_test()
    # Force compile via first call.
    assert vocab.matches_sourcetype("cisco:ise:auth") is True
    first = vocab._glob_re
    # Subsequent calls reuse the same compiled object.
    assert vocab.matches_sourcetype("vmware:nsxt:syslog") is True
    assert vocab._glob_re is first


def test_audit_skips_glob_matching_sourcetypes() -> None:
    """End-to-end: a sourcetype that only matches a glob is NOT flagged."""
    from splunk_uc.audits.spl_references import (
        Vocabulary,
        check_one_spl_field,
    )

    vocab = Vocabulary(
        commands={"search", "stats"},
        macros=set(),
        sourcetypes=set(),  # no literal "cisco:ise:auth"
        sourcetype_glob_patterns={"cisco:ise:*"},
        indexes={"main"},
        datamodel_paths=set(),
        lookups=set(),
        eval_functions=set(),
        stats_functions={"count"},
        cim_models=set(),
        sources=[],
    )
    findings = check_one_spl_field(
        uc_id="0.0.0",
        file_label="test.json",
        field="spl",
        spl='index=main sourcetype="cisco:ise:auth" | stats count',
        vocab=vocab,
        declared_sourcetypes=set(),
        declared_indexes=set(),
    )
    cats = [f.category for f in findings]
    assert "unknown-sourcetype" not in cats, (
        f"glob-matching sourcetype should not be flagged; got {findings!r}"
    )


# ---------------------------------------------------------------------------
# build_spl_reference: the new corpus readers
# ---------------------------------------------------------------------------


def test_build_script_routes_globs_and_literals() -> None:
    """Wildcard sourcetypes go to ``sourcetype_glob_patterns``, plain ones to ``sourcetypes``."""
    from tools.research.build_spl_reference import _add_sourcetype, _new_state

    state = _new_state()
    _add_sourcetype(state, "aws:cloudtrail")
    _add_sourcetype(state, "cisco:ise:*")
    _add_sourcetype(state, "*365:cas:api")
    _add_sourcetype(state, "")  # ignored
    _add_sourcetype(state, "<<placeholder>>")  # ignored

    assert state["sourcetypes"] == {"aws:cloudtrail"}
    assert state["sourcetype_glob_patterns"] == {"cisco:ise:*", "*365:cas:api"}


def test_build_script_state_has_new_buckets() -> None:
    """``_new_state`` must include the new corpus buckets so readers don't KeyError."""
    from tools.research.build_spl_reference import _new_state

    s = _new_state()
    for k in (
        "sourcetypes",
        "sourcetype_glob_patterns",
        "cim_models",
        "cim_tags",
    ):
        assert k in s, f"missing bucket {k!r}"


def test_build_script_serialise_includes_new_buckets() -> None:
    """``_serialise`` exposes the new buckets in the output JSON shape."""
    from tools.research.build_spl_reference import _new_state, _serialise

    payload = _serialise(_new_state(), [])
    for k in (
        "sourcetype_glob_patterns",
        "cim_models",
        "cim_tags",
    ):
        assert k in payload, f"missing serialised key {k!r}"
        assert payload[k] == []  # empty state ⇒ empty arrays
