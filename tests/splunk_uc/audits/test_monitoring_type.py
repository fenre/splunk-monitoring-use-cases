"""Unit tests pinning ``splunk_uc.audits.monitoring_type``.

The audit walks every UC sidecar in the JSON SSOT and surfaces three
classes of issue on the ``monitoringType`` array field:

1. **MED** ``monitoring-type-empty`` — the field is missing or empty.
2. **LOW** ``monitoring-type-unknown-token`` — the field contains a
   non-canonical category token. The schema enum catches most spellings;
   this is a safety net for legacy JSON edits.
3. **HIGH** ``monitoring-type-security-mismatch`` — the UC carries a
   genuine ATT&CK ``attackTechniques`` mapping (canonical ``Txxxx`` /
   ``TAxxxx`` tokens, NOT ``N/A (...)``) but its ``monitoringType`` does
   not include ``Security``.

The ``--check`` flag flips the exit code to 1 only on HIGH findings;
MED/LOW are reported but never block CI.

These tests are hermetic — each one builds a synthetic ``content/``
tree under ``tmp_path`` and monkey-patches the ``_uc_walk`` module's
``REPO`` and ``CONTENT`` constants so ``iter_uc_sidecars()`` reads our
fixture instead of the live filesystem.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import _uc_walk
from splunk_uc.audits import monitoring_type as mt


class MakeUC(Protocol):
    """Factory protocol for writing a UC sidecar."""

    def __call__(
        self,
        uc_id: str,
        *,
        monitoring_type: Any = ...,
        attack_techniques: Any = ...,
        category: int = 1,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a fake repo skeleton and rewire ``_uc_walk`` constants."""
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    monkeypatch.setattr(_uc_walk, "REPO", tmp_path)
    monkeypatch.setattr(_uc_walk, "CONTENT", content_dir)
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Return a factory that creates ``content/cat-N-foo/UC-X.Y.Z.json`` files."""

    def _make(
        uc_id: str,
        *,
        monitoring_type: Any = ...,
        attack_techniques: Any = ...,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category}-foo"
        cat_dir.mkdir(exist_ok=True)
        payload: dict[str, Any] = {"id": uc_id}
        if monitoring_type is not ...:
            payload["monitoringType"] = monitoring_type
        if attack_techniques is not ...:
            payload["attackTechniques"] = attack_techniques
        path = cat_dir / f"UC-{uc_id}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    return _make


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_re_mitre_token_matches_canonical_technique_id() -> None:
    """``TXXXX`` and ``TXXXX.YYY`` canonical IDs match."""
    assert mt.RE_MITRE_TOKEN.match("T1234")
    assert mt.RE_MITRE_TOKEN.match("T1234.001")
    assert mt.RE_MITRE_TOKEN.match("TA0001")


def test_re_mitre_token_rejects_non_canonical_input() -> None:
    """Lowercase, short, prefixed, suffixed forms don't match."""
    assert not mt.RE_MITRE_TOKEN.match("t1234")
    assert not mt.RE_MITRE_TOKEN.match("T123")
    assert not mt.RE_MITRE_TOKEN.match("XT1234")
    assert not mt.RE_MITRE_TOKEN.match("T1234X")
    assert not mt.RE_MITRE_TOKEN.match("T1234.12")  # subtechnique requires 3 digits
    assert not mt.RE_MITRE_TOKEN.match("")


def test_re_mitre_na_matches_na_variants() -> None:
    """``N/A`` and ``NA`` with optional parenthetical match."""
    assert mt.RE_MITRE_NA.match("N/A")
    assert mt.RE_MITRE_NA.match("NA")
    assert mt.RE_MITRE_NA.match("n/a")
    assert mt.RE_MITRE_NA.match("N/A (No technique applicable)")
    assert mt.RE_MITRE_NA.match("NA (defensive)")
    # Trailing whitespace tolerated.
    assert mt.RE_MITRE_NA.match("N/A  ")


def test_re_mitre_na_rejects_unrelated_strings() -> None:
    """Real ATT&CK tokens and gibberish don't match ``N/A``."""
    assert not mt.RE_MITRE_NA.match("T1234")
    assert not mt.RE_MITRE_NA.match("NAH")
    assert not mt.RE_MITRE_NA.match("Not applicable")


def test_canonical_tokens_contains_expected_set() -> None:
    """``CANONICAL_TOKENS`` is a frozenset-like set of well-known categories."""
    expected_subset = {
        "Security",
        "Performance",
        "Availability",
        "Compliance",
        "Operations",
    }
    assert expected_subset.issubset(mt.CANONICAL_TOKENS)
    assert isinstance(mt.CANONICAL_TOKENS, set)


def test_canonical_tokens_has_thirty_entries() -> None:
    """Pin the exact size so additions/removals are caught by review."""
    assert len(mt.CANONICAL_TOKENS) == 30


def test_token_normalisation_includes_operational_alias() -> None:
    """``Operational`` is normalised to ``Operations`` per documented contract."""
    assert mt.TOKEN_NORMALISATION == {"Operational": "Operations"}


# ---------------------------------------------------------------------------
# Finding NamedTuple
# ---------------------------------------------------------------------------


def test_finding_namedtuple_has_six_fields() -> None:
    """Finding carries severity/kind/uc_id/file/message/snippet."""
    finding = mt.Finding(
        severity="HIGH",
        kind="monitoring-type-security-mismatch",
        uc_id="UC-1.1.1",
        file="UC-1.1.1.json",
        message="msg",
        snippet="Performance",
    )
    assert finding.severity == "HIGH"
    assert finding.kind == "monitoring-type-security-mismatch"
    assert finding.uc_id == "UC-1.1.1"
    assert finding.file == "UC-1.1.1.json"
    assert finding.message == "msg"
    assert finding.snippet == "Performance"


def test_finding_snippet_defaults_to_empty_string() -> None:
    """``snippet`` field defaults to ``""``."""
    finding = mt.Finding(
        severity="MED",
        kind="monitoring-type-empty",
        uc_id="UC-1.1.1",
        file="UC-1.1.1.json",
        message="msg",
    )
    assert finding.snippet == ""


# ---------------------------------------------------------------------------
# _has_real_mitre_mapping
# ---------------------------------------------------------------------------


def test_has_real_mitre_mapping_true_for_canonical_token() -> None:
    """A canonical ``TXXXX`` token returns True."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["T1234"]}) is True


def test_has_real_mitre_mapping_true_for_subtechnique() -> None:
    """A canonical ``TXXXX.YYY`` subtechnique returns True."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["T1234.001"]}) is True


def test_has_real_mitre_mapping_true_for_tactic_id() -> None:
    """A canonical ``TAXXXX`` tactic returns True."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["TA0001"]}) is True


def test_has_real_mitre_mapping_false_for_na() -> None:
    """An ``N/A`` token does NOT count as a real mapping."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["N/A"]}) is False
    assert mt._has_real_mitre_mapping({"attackTechniques": ["N/A (no technique)"]}) is False


def test_has_real_mitre_mapping_false_for_empty_list() -> None:
    """Empty list returns False."""
    assert mt._has_real_mitre_mapping({"attackTechniques": []}) is False


def test_has_real_mitre_mapping_false_when_field_missing() -> None:
    """Missing ``attackTechniques`` field returns False."""
    assert mt._has_real_mitre_mapping({}) is False


def test_has_real_mitre_mapping_skips_non_string_entries() -> None:
    """Non-string entries (int, None, list) are silently skipped."""
    payload: dict[str, Any] = {
        "attackTechniques": [42, None, ["nested"], "T1234"],
    }
    assert mt._has_real_mitre_mapping(payload) is True


def test_has_real_mitre_mapping_strips_whitespace_around_token() -> None:
    """Surrounding whitespace is stripped before matching."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["  T1234  "]}) is True


def test_has_real_mitre_mapping_false_for_non_canonical_string() -> None:
    """``T123`` (only 3 digits) does NOT match the regex."""
    assert mt._has_real_mitre_mapping({"attackTechniques": ["T123"]}) is False


def test_has_real_mitre_mapping_true_when_mixed_na_and_real() -> None:
    """A list with N/A entries AND real tokens returns True."""
    payload = {"attackTechniques": ["N/A (placeholder)", "T1234"]}
    assert mt._has_real_mitre_mapping(payload) is True


# ---------------------------------------------------------------------------
# _check_uc
# ---------------------------------------------------------------------------


def test_check_uc_flags_missing_monitoring_type_as_med() -> None:
    """Missing ``monitoringType`` surfaces as MED ``monitoring-type-empty``."""
    findings = mt._check_uc("UC-1.1.1", "UC-1.1.1.json", {})
    assert len(findings) == 1
    assert findings[0].severity == "MED"
    assert findings[0].kind == "monitoring-type-empty"


def test_check_uc_flags_empty_monitoring_type_as_med() -> None:
    """An empty list surfaces as MED."""
    findings = mt._check_uc("UC-1.1.1", "UC-1.1.1.json", {"monitoringType": []})
    assert len(findings) == 1
    assert findings[0].kind == "monitoring-type-empty"


def test_check_uc_returns_no_finding_on_clean_payload() -> None:
    """Canonical token + no ATT&CK techniques → no findings."""
    findings = mt._check_uc("UC-1.1.1", "UC-1.1.1.json", {"monitoringType": ["Security"]})
    assert findings == []


def test_check_uc_flags_unknown_token_as_low() -> None:
    """Non-canonical token surfaces as LOW ``monitoring-type-unknown-token``."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": ["Securtiy"]},
    )
    assert len(findings) >= 1
    low_findings = [f for f in findings if f.kind == "monitoring-type-unknown-token"]
    assert len(low_findings) == 1
    assert low_findings[0].severity == "LOW"


def test_check_uc_includes_normalisation_advice_for_known_alias() -> None:
    """``Operational`` token surfaces with ``'Operational' -> 'Operations'`` advice."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": ["Operational"]},
    )
    low_findings = [f for f in findings if f.kind == "monitoring-type-unknown-token"]
    assert len(low_findings) == 1
    assert "'Operational' -> 'Operations'" in low_findings[0].message


def test_check_uc_lists_canonical_set_in_unknown_token_message() -> None:
    """Unknown-token message ends with the sorted canonical set listing."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": ["Bogus"]},
    )
    low = next(f for f in findings if f.kind == "monitoring-type-unknown-token")
    assert "Canonical set:" in low.message
    # First and last canonical tokens alphabetically are 'Analytics' and 'Vulnerability'.
    assert "Analytics" in low.message
    assert "Vulnerability" in low.message


def test_check_uc_snippet_carries_full_token_list_for_unknown() -> None:
    """``snippet`` reflects the full provided token list, not just the unknown."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": ["Security", "Bogus"]},
    )
    low = next(f for f in findings if f.kind == "monitoring-type-unknown-token")
    assert low.snippet == "Security, Bogus"


def test_check_uc_flags_security_mismatch_as_high() -> None:
    """ATT&CK token + no ``Security`` in monitoringType → HIGH."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "monitoringType": ["Performance"],
            "attackTechniques": ["T1234"],
        },
    )
    high = [f for f in findings if f.kind == "monitoring-type-security-mismatch"]
    assert len(high) == 1
    assert high[0].severity == "HIGH"


def test_check_uc_does_not_flag_when_security_present() -> None:
    """``Security`` in monitoringType suppresses the HIGH finding."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "monitoringType": ["Security", "Performance"],
            "attackTechniques": ["T1234"],
        },
    )
    assert all(f.kind != "monitoring-type-security-mismatch" for f in findings)


def test_check_uc_security_match_is_case_insensitive() -> None:
    """``security`` (lowercase) also satisfies the HIGH check (via ``t.lower()``)."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "monitoringType": ["security"],
            "attackTechniques": ["T1234"],
        },
    )
    assert all(f.kind != "monitoring-type-security-mismatch" for f in findings)
    # But the lowercase form is NOT in CANONICAL_TOKENS, so LOW fires.
    assert any(f.kind == "monitoring-type-unknown-token" for f in findings)


def test_check_uc_does_not_flag_when_attack_is_na_only() -> None:
    """``N/A``-only ``attackTechniques`` does not trigger HIGH."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "monitoringType": ["Performance"],
            "attackTechniques": ["N/A (placeholder)"],
        },
    )
    assert all(f.kind != "monitoring-type-security-mismatch" for f in findings)


def test_check_uc_can_produce_two_findings_low_and_high() -> None:
    """A UC can surface a LOW (unknown token) AND a HIGH (security mismatch) together."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {
            "monitoringType": ["Operational"],
            "attackTechniques": ["T1234"],
        },
    )
    kinds = {f.kind for f in findings}
    assert "monitoring-type-unknown-token" in kinds
    assert "monitoring-type-security-mismatch" in kinds


def test_check_uc_skips_non_string_tokens() -> None:
    """Non-string entries in ``monitoringType`` are silently filtered."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": [None, 42, "Security"]},
    )
    assert findings == []  # only "Security" is left, which is canonical


def test_check_uc_treats_only_non_string_as_empty() -> None:
    """If filtering leaves no string tokens, MED ``empty`` fires."""
    findings = mt._check_uc(
        "UC-1.1.1",
        "UC-1.1.1.json",
        {"monitoringType": [None, 42]},
    )
    assert len(findings) == 1
    assert findings[0].kind == "monitoring-type-empty"


# ---------------------------------------------------------------------------
# main() — happy path
# ---------------------------------------------------------------------------


def test_main_returns_0_when_clean_payload(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean UC with canonical token → exit 0."""
    make_uc("1.1.1", monitoring_type=["Security"])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "Sidecars scanned: 1" in captured.out


def test_main_returns_0_on_empty_content_tree(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Empty content/ tree → exit 0 with `Sidecars scanned: 0`."""
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "Sidecars scanned: 0" in captured.out


def test_main_argv_none_uses_sys_argv_default(
    make_uc: MakeUC,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-monitoring-type"])
    make_uc("1.1.1", monitoring_type=["Security"])
    assert mt.main(None) == 0


def test_main_help_exits_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits with 0 and prints argparse help text."""
    with pytest.raises(SystemExit) as exc:
        mt.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--check" in captured.out


# ---------------------------------------------------------------------------
# main() — finding-surface output
# ---------------------------------------------------------------------------


def test_main_prints_header_with_separator(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Output starts with a ``=``-bar banner."""
    make_uc("1.1.1", monitoring_type=["Security"])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "=" * 72 in captured.out
    assert "Monitoring-type audit (content/cat-*/UC-*.json)" in captured.out


def test_main_renders_findings_by_severity_tally(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """The severity-tally line lists all severities in sorted order."""
    make_uc("1.1.1", monitoring_type=["Bogus"])  # LOW
    make_uc("1.1.2", monitoring_type=[])  # MED
    make_uc(
        "1.1.3",
        monitoring_type=["Performance"],
        attack_techniques=["T1234"],
    )  # HIGH
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "HIGH=1" in captured.out
    assert "LOW=1" in captured.out
    assert "MED=1" in captured.out


def test_main_renders_findings_by_kind_count_sorted_descending(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """The by-kind block sorts by count descending."""
    make_uc("1.1.1", monitoring_type=[])  # MED
    make_uc("1.1.2", monitoring_type=[])  # MED
    make_uc("1.1.3", monitoring_type=["Bogus"])  # LOW
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    # Find the by-kind block lines
    out = captured.out
    empty_idx = out.find("monitoring-type-empty")
    unknown_idx = out.find("monitoring-type-unknown-token")
    assert empty_idx >= 0
    assert unknown_idx >= 0
    assert empty_idx < unknown_idx  # higher count appears first


def test_main_prints_findings_section_with_dash_separator(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """The findings detail block has a ``-``-bar separator."""
    make_uc("1.1.1", monitoring_type=["Bogus"])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "FINDINGS:" in captured.out
    assert "-" * 72 in captured.out


def test_main_orders_findings_high_then_med_then_low(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Findings in the detail block are sorted HIGH, MED, LOW."""
    make_uc("1.1.1", monitoring_type=["Bogus"])  # LOW
    make_uc("1.1.2", monitoring_type=[])  # MED
    make_uc(
        "1.1.3",
        monitoring_type=["Performance"],
        attack_techniques=["T1234"],
    )  # HIGH
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    out = captured.out
    high_idx = out.find("[HIGH]")
    med_idx = out.find("[MED]")
    low_idx = out.find("[LOW]")
    assert 0 <= high_idx < med_idx < low_idx


def test_main_prints_snippet_when_provided(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Findings carrying a snippet print a ``snippet:`` line."""
    make_uc("1.1.1", monitoring_type=["Bogus"])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "snippet:" in captured.out


def test_main_truncates_snippet_at_200_chars(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """Snippet is truncated at 200 characters via ``f.snippet[:200]``."""
    long_tokens = [f"Bogus{i}" for i in range(50)]  # > 200 chars
    make_uc("1.1.1", monitoring_type=long_tokens)
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    snippet_line = next(
        line for line in captured.out.splitlines() if line.startswith("        snippet:")
    )
    # The line content after the prefix is at most 200 chars.
    content = snippet_line[len("        snippet: ") :]
    assert len(content) == 200


def test_main_does_not_print_snippet_when_field_empty(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """When ``snippet=""`` (e.g. MED empty finding), no snippet line is printed."""
    make_uc("1.1.1", monitoring_type=[])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    # The only finding is MED empty with snippet="" — no snippet line should appear
    findings_block = captured.out.split("FINDINGS:")[1]
    assert "snippet:" not in findings_block


# ---------------------------------------------------------------------------
# main() — --check mode
# ---------------------------------------------------------------------------


def test_main_check_returns_0_when_no_high(make_uc: MakeUC) -> None:
    """``--check`` with only MED/LOW findings still exits 0."""
    make_uc("1.1.1", monitoring_type=[])  # MED
    make_uc("1.1.2", monitoring_type=["Bogus"])  # LOW
    assert mt.main(["--check"]) == 0


def test_main_check_returns_1_when_high_present(make_uc: MakeUC) -> None:
    """``--check`` with a HIGH finding exits 1."""
    make_uc(
        "1.1.1",
        monitoring_type=["Performance"],
        attack_techniques=["T1234"],
    )
    assert mt.main(["--check"]) == 1


def test_main_without_check_always_returns_0_even_when_high(
    make_uc: MakeUC,
) -> None:
    """Without ``--check``, HIGH findings still exit 0 (informational mode)."""
    make_uc(
        "1.1.1",
        monitoring_type=["Performance"],
        attack_techniques=["T1234"],
    )
    assert mt.main([]) == 0


# ---------------------------------------------------------------------------
# main() — sidecar id rendering
# ---------------------------------------------------------------------------


def test_main_renders_uc_id_with_uc_prefix(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """UC IDs render as ``UC-X.Y.Z`` (prefix added in ``main()``)."""
    make_uc("1.1.1", monitoring_type=[])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "UC-1.1.1" in captured.out


def test_main_renders_unknown_id_for_missing_id_field(
    fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When ``id`` is missing from payload, ``UC-<unknown>`` is rendered."""
    cat_dir = fake_repo / "content" / "cat-1-foo"
    cat_dir.mkdir()
    # Payload without "id" field.
    (cat_dir / "UC-orphan.json").write_text(
        json.dumps({"monitoringType": []}),
        encoding="utf-8",
    )
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "UC-<unknown>" in captured.out


def test_main_reports_file_basename_only(
    make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
) -> None:
    """The ``file:`` field on the finding is the basename only (``path.name``)."""
    make_uc("1.1.1", monitoring_type=[])
    assert mt.main([]) == 0
    captured = capsys.readouterr()
    assert "(UC-1.1.1.json)" in captured.out
    # The full path should NOT appear.
    assert "/cat-1-foo/UC-1.1.1.json" not in captured.out
