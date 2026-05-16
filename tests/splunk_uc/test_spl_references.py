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
