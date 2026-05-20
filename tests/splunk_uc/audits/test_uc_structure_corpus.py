"""End-to-end corpus tests for ``splunk_uc.audits.uc_structure``.

The legacy unit tests at ``tests/scripts/test_audit_uc_structure_json.py``
cover the per-UC ``audit_uc_json`` and ``_load_baseline`` primitives at
~10% of the module. This file lifts coverage by exercising the two
higher-level orchestration paths:

* ``_audit_json_corpus`` — the corpus walker (glob, parse, sample-or-full,
  baseline-filter, print);
* ``main`` — the CLI entry point that owns argument parsing, dispatch to
  ``_audit_json_corpus``, the summary block, and the exit-code contract.

We monkey-patch the module-level ``CONTENT`` glob so each test gets a
hermetic tmp_path corpus instead of touching the real catalogue. Every
test asserts both the structured return value AND the human-readable
stdout block — those two surfaces are what CI and developers actually
consume.
"""

from __future__ import annotations

import json as jsonlib
import os
from pathlib import Path

import pytest

from splunk_uc.audits import uc_structure as audit


def _good_uc(uc_id: str = "1.2.3") -> dict[str, object]:
    return {
        "id": uc_id,
        "title": "Detect privilege escalation in Linux audit logs",
        "criticality": "high",
        "difficulty": "intermediate",
        "monitoringType": ["Security"],
        "value": "Catches root-elevation events that bypass sudo logging.",
        "app": "Splunk_TA_nix",
        "dataSources": "auditd",
        "spl": "search index=os sourcetype=linux_audit | stats count by user",
        "implementation": "Enable auditd; ingest via Splunk_TA_nix.",
        "visualization": "Single value with sparkline",
        "cimModels": ["Authentication"],
        "grandmaExplanation": (
            "We watch for someone secretly becoming an administrator on the "
            "machine, even if they tried to hide it."
        ),
    }


@pytest.fixture
def temp_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Build a fake ``content/cat-*/UC-*.json`` corpus rooted at ``tmp_path``.

    Returns the corpus root (``<tmp_path>/content``). Monkey-patches the
    audit module's ``CONTENT`` glob to point at this root and ``REPO_ROOT``
    to ``tmp_path`` so the rel-path computation in ``audit_uc_json`` stays
    tidy.
    """

    root = tmp_path / "content"
    (root / "cat-99-fixture").mkdir(parents=True)
    monkeypatch.setattr(
        audit,
        "CONTENT",
        str(root / "cat-*" / "UC-*.json"),
    )
    monkeypatch.setattr(audit, "REPO_ROOT", str(tmp_path))
    return root


def _write_uc(corpus_root: Path, uc_id: str, payload: dict | str) -> Path:
    """Write a single UC sidecar. ``payload=str`` writes raw text (for
    parse-error tests). ``payload=dict`` writes pretty JSON."""

    cat_dir = corpus_root / "cat-99-fixture"
    p = cat_dir / f"UC-{uc_id}.json"
    if isinstance(payload, str):
        p.write_text(payload, encoding="utf-8")
    else:
        p.write_text(jsonlib.dumps(payload, indent=2), encoding="utf-8")
    return p


# --------------------------------------------------------------------- #
# audit_uc_json — per-UC primitive, regression coverage for the
# field-level branches that the corpus walker exercises only at the
# happy path.
# --------------------------------------------------------------------- #


class TestAuditUcJsonFieldChecks:
    """Pin every issue-emitting branch in ``audit_uc_json``.

    The existing corpus tests assert on the orchestration layer; this
    class fires the primitive directly so a future refactor of the
    rule set cannot silently drop a check.
    """

    def test_id_mismatch_with_filename_is_flagged(self) -> None:
        # File is UC-1.1.1.json but the JSON ``id`` claims 9.9.9.
        payload = _good_uc("9.9.9")
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("does not match filename" in i for i in issues)

    def test_empty_string_required_field_is_flagged(self) -> None:
        payload = _good_uc("1.1.1")
        payload["value"] = "   "  # whitespace-only is "empty" too
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("empty required field 'value'" in i for i in issues)

    def test_empty_list_required_field_is_flagged(self) -> None:
        payload = _good_uc("1.1.1")
        # monitoringType is a list field and is NOT in
        # JSON_FIELDS_ALLOW_EMPTY_LIST, so an empty list MUST be flagged.
        payload["monitoringType"] = []
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("empty required field 'monitoringType'" in i for i in issues)

    def test_empty_list_is_allowed_for_cim_models(self) -> None:
        payload = _good_uc("1.1.1")
        payload["cimModels"] = []  # explicitly allowed
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert not any("cimModels" in i for i in issues)

    def test_null_required_field_is_flagged(self) -> None:
        payload = _good_uc("1.1.1")
        payload["visualization"] = None
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("null required field 'visualization'" in i for i in issues)

    def test_legacy_markdown_criticality_is_flagged_with_hint(self) -> None:
        payload = _good_uc("1.1.1")
        payload["criticality"] = "🔴 Critical"
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("legacy markdown" in i and "criticality" in i for i in issues)

    def test_unknown_criticality_value_is_flagged_as_invalid(self) -> None:
        payload = _good_uc("1.1.1")
        payload["criticality"] = "URGENT"
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("invalid criticality" in i for i in issues)

    def test_legacy_markdown_difficulty_is_flagged_with_hint(self) -> None:
        payload = _good_uc("1.1.1")
        payload["difficulty"] = "🟠 Advanced"
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("legacy markdown" in i and "difficulty" in i for i in issues)

    def test_unknown_difficulty_value_is_flagged_as_invalid(self) -> None:
        payload = _good_uc("1.1.1")
        payload["difficulty"] = "BRUTAL"
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("invalid difficulty" in i for i in issues)

    def test_non_string_spl_is_flagged(self) -> None:
        payload = _good_uc("1.1.1")
        payload["spl"] = ["index=foo", "| stats count"]  # must be string
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert any("spl must be a string" in i for i in issues)

    def test_empty_string_spl_is_flagged(self) -> None:
        payload = _good_uc("1.1.1")
        # Bypass the empty-required-field check by setting spl to
        # whitespace-only — that still hits the spl-specific guard.
        payload["spl"] = "   "
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        # Both the "empty required field" check and the spl-specific
        # check fire on whitespace-only strings. Pin BOTH so the
        # author can see which guard triggered.
        assert any("empty required field 'spl'" in i for i in issues)
        assert any(i.endswith("spl is empty") for i in issues)

    def test_non_string_criticality_skips_enum_checks(self) -> None:
        """If ``criticality`` is something exotic (e.g. an int or list)
        the schema-level type check fails earlier; this audit short-
        circuits the value-enum guard. Pin the False branch of the
        ``isinstance(crit, str) and crit`` guard so a refactor that
        starts coercing types cannot silently start emitting bogus
        invalid-criticality errors."""
        payload = _good_uc("1.1.1")
        payload["criticality"] = 42
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        # No "invalid criticality" issue should appear because we
        # never reached the enum check.
        assert not any("invalid criticality" in i for i in issues)

    def test_non_string_difficulty_skips_enum_checks(self) -> None:
        payload = _good_uc("1.1.1")
        payload["difficulty"] = ["intermediate"]
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        assert not any("invalid difficulty" in i for i in issues)

    def test_missing_spl_field_skips_string_check(self) -> None:
        """When ``spl`` is absent entirely, the per-field 'missing
        required field' rule above takes care of it. The spl-specific
        guard is skipped because ``payload.get('spl')`` is None. Pin
        the None branch so a refactor that defaults to ``""`` cannot
        silently start emitting double-issue noise."""
        payload = _good_uc("1.1.1")
        del payload["spl"]
        issues = audit.audit_uc_json("/repo/content/cat-1/UC-1.1.1.json", payload)
        # The "missing required field" issue is present...
        assert any("missing required field 'spl'" in i for i in issues)
        # ...but NOT the spl-specific "spl must be a string" / "spl is empty".
        assert not any("spl must be a string" in i for i in issues)
        assert not any(i.endswith("spl is empty") for i in issues)


# --------------------------------------------------------------------- #
# _audit_json_corpus — happy and unhappy paths
# --------------------------------------------------------------------- #


def test_corpus_all_good_returns_zero_issues(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    _write_uc(temp_corpus, "1.1.2", _good_uc("1.1.2"))

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)

    assert (issues, total) == (0, 2)
    out = capsys.readouterr().out
    assert "Sidecars scanned: 2" in out
    assert "Total raw JSON issues:                   0" in out
    assert "No JSON issues vs. baseline." in out


def test_corpus_surfaces_field_violations(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A UC missing ``cimModels`` must produce one new issue + a stdout
    line referencing the field name."""

    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    _write_uc(temp_corpus, "1.1.1", payload)

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)

    assert total == 1
    assert issues == 1
    out = capsys.readouterr().out
    assert "missing required field 'cimModels'" in out


def test_corpus_reports_parse_errors_without_crashing(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    _write_uc(temp_corpus, "1.1.2", "{ this is not valid json")

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)

    # Parse-error UC dropped from sidecars (so total=1) but a parse-error
    # entry is still counted as a new issue.
    assert total == 1
    assert issues == 1
    out = capsys.readouterr().out
    assert "failed to parse" in out
    assert "parse errors: 1" in out


def test_corpus_rejects_non_object_top_level(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(temp_corpus, "1.1.1", "[1, 2, 3]")

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)

    assert total == 0
    assert issues == 1
    out = capsys.readouterr().out
    assert "top-level must be a JSON object" in out
    assert "got list" in out


def test_corpus_baseline_filters_known_issues(
    temp_corpus: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A baseline entry matching the raw issue line must drop it from
    ``new_issues`` and the summary."""

    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    uc_path = _write_uc(temp_corpus, "1.1.1", payload)

    # First pass without baseline to capture the exact issue text.
    args0 = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues0, _ = audit._audit_json_corpus(args0)
    capsys.readouterr()  # discard
    assert issues0 == 1

    raw_line = audit.audit_uc_json(str(uc_path), payload)[0]
    baseline_path = tmp_path / "baseline.txt"
    baseline_path.write_text(raw_line + "\n", encoding="utf-8")

    args1 = audit.argparse.Namespace(
        full=False, baseline=str(baseline_path), print_baseline=False
    )
    new_issues, _ = audit._audit_json_corpus(args1)
    assert new_issues == 0
    out = capsys.readouterr().out
    assert "Baseline: 1 known issues filtered." in out
    assert "No JSON issues vs. baseline." in out


def test_corpus_reports_fixed_baseline_lines(
    temp_corpus: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Baseline lines that no longer appear in the raw issue list must
    show up under "FIXED BASELINE LINES (delete...)" so the author
    deletes them in the same PR."""

    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    stale_issue = (
        "1.1.1 (content/cat-99-fixture/UC-1.1.1.json): "
        "missing required field 'cimModels'"
    )
    baseline_path = tmp_path / "baseline.txt"
    baseline_path.write_text(stale_issue + "\n", encoding="utf-8")

    args = audit.argparse.Namespace(
        full=False, baseline=str(baseline_path), print_baseline=False
    )
    new_issues, total = audit._audit_json_corpus(args)

    assert (new_issues, total) == (0, 1)
    out = capsys.readouterr().out
    assert "FIXED BASELINE LINES" in out
    assert stale_issue in out


def test_corpus_print_baseline_emits_raw_issues_and_exits(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--print-baseline`` must print every raw issue sorted to stdout
    and return (0, total) WITHOUT printing the summary block."""

    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    _write_uc(temp_corpus, "1.1.1", payload)

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=True
    )
    issues, total = audit._audit_json_corpus(args)
    assert (issues, total) == (0, 1)
    out = capsys.readouterr().out

    assert "Sidecars scanned" not in out  # summary block suppressed
    assert "missing required field 'cimModels'" in out


def test_corpus_handles_empty_glob(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No UC files → no issues, no crash, no parse errors."""

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)
    assert (issues, total) == (0, 0)
    out = capsys.readouterr().out
    assert "Sidecars scanned: 0" in out


# --------------------------------------------------------------------- #
# _load_baseline — extra coverage of the edge paths
# --------------------------------------------------------------------- #


def test_load_baseline_missing_file_returns_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = audit._load_baseline("/no/such/baseline.txt")
    assert out == set()
    captured = capsys.readouterr().err
    assert "does not exist; ignoring" in captured


def test_load_baseline_strips_blanks_and_comments(tmp_path: Path) -> None:
    bl = tmp_path / "baseline.txt"
    bl.write_text(
        "# leading comment\n"
        "\n"
        "issue-1\n"
        "  # indented comment\n"
        "issue-2\n",
        encoding="utf-8",
    )
    loaded = audit._load_baseline(str(bl))
    assert loaded == {"issue-1", "issue-2"}


def test_load_baseline_none_path_returns_empty() -> None:
    assert audit._load_baseline(None) == set()


# --------------------------------------------------------------------- #
# main() — exit-code contract
# --------------------------------------------------------------------- #


def test_main_returns_zero_when_clean(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    rc = audit.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "All audited UCs pass." in out
    assert "SUMMARY" in out


def test_main_returns_one_when_new_issues_present(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    _write_uc(temp_corpus, "1.1.1", payload)

    rc = audit.main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "json SSOT: 1 UCs, 1 new issues vs. baseline" in out


def test_main_print_baseline_returns_zero_even_with_issues(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--print-baseline`` is a refresh-the-baseline tool; it must NOT
    fail the build even when raw issues exist."""

    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    _write_uc(temp_corpus, "1.1.1", payload)

    rc = audit.main(["--print-baseline"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "missing required field 'cimModels'" in out
    assert "SUMMARY" not in out  # the early-return path skips the summary


def test_main_empty_baseline_string_disables_filtering(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Passing ``--baseline ''`` must clear the default baseline path,
    not stat the empty string."""

    payload = _good_uc("1.1.1")
    del payload["cimModels"]
    _write_uc(temp_corpus, "1.1.1", payload)

    rc = audit.main(["--baseline", ""])
    out = capsys.readouterr().out

    # The default baseline path is bypassed entirely (no "does not exist"
    # warning) and the audit reports the violation as a NEW issue.
    err = capsys.readouterr().err
    assert "does not exist; ignoring" not in err
    assert rc == 1
    assert "1 new issues vs. baseline" in out


def test_main_respects_full_flag_when_population_below_threshold(
    temp_corpus: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Below 5000 UCs the audit always runs full-scan regardless of the
    flag — must not say "Sampling:"."""

    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    rc = audit.main(["--full"])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Sampling:" not in out
    assert (
        "All 1 UCs checked (population at or under threshold 5000)" in out
        or "Full scan" in out
    )


# --------------------------------------------------------------------- #
# audit_uc_json — gap closures (criticality/difficulty edge paths
# untouched by the legacy unit tests at tests/scripts/...)
# --------------------------------------------------------------------- #


def test_audit_uc_json_invalid_criticality_not_emoji(tmp_path: Path) -> None:
    """A criticality string that is neither a valid enum nor a legacy
    markdown emoji must produce the ``invalid criticality`` issue
    (covers the else-branch on line 120-124 of ``uc_structure.py``)."""

    payload = _good_uc("1.1.1")
    payload["criticality"] = "extreme"  # not in VALID, not an emoji
    p = tmp_path / "UC-1.1.1.json"
    p.touch()
    issues = audit.audit_uc_json(str(p), payload)
    assert any("invalid criticality 'extreme'" in i for i in issues), issues


def test_audit_uc_json_legacy_emoji_difficulty_rejected(
    tmp_path: Path,
) -> None:
    """The legacy markdown emoji form of difficulty must produce the
    ``uses the legacy markdown emoji form`` issue (covers the
    legacy-emoji branch on line 129-134 of ``uc_structure.py``)."""

    payload = _good_uc("1.1.1")
    payload["difficulty"] = "🔵 Intermediate"  # legacy emoji form
    p = tmp_path / "UC-1.1.1.json"
    p.touch()
    issues = audit.audit_uc_json(str(p), payload)
    assert any("uses the legacy markdown emoji form" in i for i in issues), (
        issues
    )


# --------------------------------------------------------------------- #
# Sampling / threshold messaging — exercise the >LARGE_THRESHOLD branches
# by monkey-patching the constants to small numbers so we don't have to
# generate 5,000 UC files on every CI run.
# --------------------------------------------------------------------- #


def test_corpus_samples_when_total_exceeds_threshold(
    temp_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When total > LARGE_THRESHOLD and ``--full`` is NOT set, the
    audit must take a deterministic random sample and announce
    "Sampling: ..." (covers lines 206-208 and 230 of
    ``uc_structure.py``)."""

    monkeypatch.setattr(audit, "LARGE_THRESHOLD", 2)
    monkeypatch.setattr(audit, "SAMPLE_SIZE", 2)
    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    _write_uc(temp_corpus, "1.1.2", _good_uc("1.1.2"))
    _write_uc(temp_corpus, "1.1.3", _good_uc("1.1.3"))

    args = audit.argparse.Namespace(
        full=False, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)
    out = capsys.readouterr().out

    assert total == 3
    assert issues == 0
    assert "Sampling: 2 UCs checked (random seed=42, population>2)" in out


def test_corpus_full_scan_announces_threshold_message(
    temp_corpus: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When ``--full`` is passed AND total > LARGE_THRESHOLD, the
    audit must announce "Full scan: all N UCs checked (--full, ...)"
    (covers line 235 of ``uc_structure.py``)."""

    monkeypatch.setattr(audit, "LARGE_THRESHOLD", 1)
    _write_uc(temp_corpus, "1.1.1", _good_uc("1.1.1"))
    _write_uc(temp_corpus, "1.1.2", _good_uc("1.1.2"))

    args = audit.argparse.Namespace(
        full=True, baseline=None, print_baseline=False
    )
    issues, total = audit._audit_json_corpus(args)
    out = capsys.readouterr().out

    assert total == 2
    assert issues == 0
    assert "Full scan: all 2 UCs checked (--full, population>1)" in out
