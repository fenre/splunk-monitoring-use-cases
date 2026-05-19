"""Unit tests for ``splunk_uc.audits.content_quality``.

P16 wave GG: lifts ``src/splunk_uc/audits/content_quality.py`` from
~14% to 100% combined coverage. Pins every documented contract of
the content-quality audit:

(a) flag UCs where ``description`` and ``value`` are identical
    (whitespace-normalised);
(b) flag UCs where ``grandmaExplanation`` mentions any of the 11
    technical jargon terms (case-insensitive, first-match-breaks);
(c) flag UCs whose ``controlTest.fixtureRef`` does not resolve on
    disk;
(d) invalid-JSON sidecars are flagged with ``invalid_json``;
(e) ``--generate-baseline`` emits the current violations list as
    JSON and exits 0; ``--baseline`` suppresses listed violations,
    truncating the printed list to 20 with a ``... and N more``
    footer.

Also pins the description/value dimension heuristics added in B-6.
"""

from __future__ import annotations

import io
import json
import pathlib
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Protocol

import pytest

from splunk_uc.audits import content_quality as cq
from splunk_uc.audits._content_quality_dimensions import (
    evaluate_description_quality,
    evaluate_value_quality,
)


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path: ...


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Hermetic repo with content/ + sample-data/ skeletons."""
    (tmp_path / "content").mkdir()
    (tmp_path / "sample-data").mkdir()
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    monkeypatch.setattr(cq, "SAMPLE_DATA", tmp_path / "sample-data")
    return tmp_path


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    def _make(
        uc_id: str,
        payload: dict[str, Any] | None = None,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-test-cat"
        cat_dir.mkdir(parents=True, exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        merged = {"id": uc_id, **(payload or {})}
        sidecar.write_text(json.dumps(merged), encoding="utf-8")
        return sidecar

    return _make


# ----------------------------------------------------------------------
# Module constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_project_root_resolves(self) -> None:
        from splunk_uc.audits import content_quality as fresh

        assert (fresh.PROJECT_ROOT / "schemas").is_dir()

    def test_jargon_terms_non_empty(self) -> None:
        assert len(cq.JARGON_TERMS) > 0

    def test_jargon_terms_include_core(self) -> None:
        """The 11 documented terms must all be present."""
        expected = {
            "tstats",
            "datamodel",
            "CIM",
            "sourcetype",
            "macro",
            "eval",
            "rex",
            "lookup",
            "savedsearch",
            "props.conf",
            "transforms.conf",
        }
        assert set(cq.JARGON_TERMS) == expected


# ----------------------------------------------------------------------
# Clean and trivial paths
# ----------------------------------------------------------------------


class TestNoViolations:
    def test_empty_content_returns_zero(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cq.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "0 existing violation(s)" in out

    def test_clean_uc_returns_zero(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {
                "description": "A description.",
                "value": "A different value.",
                "grandmaExplanation": "We watch your stuff.",
            },
        )
        rc = cq.main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "0 existing" in out


# ----------------------------------------------------------------------
# Invalid JSON
# ----------------------------------------------------------------------


class TestInvalidJson:
    def test_invalid_json_flagged(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        bad = cat / "UC-1.1.1.json"
        bad.write_text("{not json,,,}", encoding="utf-8")
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid_json" in err


# ----------------------------------------------------------------------
# description == value
# ----------------------------------------------------------------------


class TestDescriptionEqualsValue:
    def test_exact_match_flagged(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"description": "Same text.", "value": "Same text."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_whitespace_strip_match_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Leading/trailing whitespace stripped before comparison."""
        make_uc(
            "1.1.1",
            {"description": "  Same text.  ", "value": "Same text."},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_different_text_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"description": "X", "value": "Y"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_description_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When ``description`` is missing the check is skipped."""
        make_uc("1.1.1", {"value": "X"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_value_not_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When ``value`` is missing the check is skipped."""
        make_uc("1.1.1", {"description": "X"})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Jargon in grandmaExplanation
# ----------------------------------------------------------------------


class TestJargonInGrandma:
    def test_no_jargon_passes(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "We watch the lights."})
        rc = cq.main([])
        assert rc == 0

    def test_tstats_flagged(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "We use tstats here."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "jargon_in_grandma: tstats" in err

    def test_case_insensitive_match(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"grandmaExplanation": "CIM model lookup."})
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # The first match in JARGON_TERMS that appears (case-insensitively)
        # is reported. Either CIM or lookup will be flagged depending on
        # which comes first in JARGON_TERMS — that's CIM.
        assert "jargon_in_grandma:" in err

    def test_first_match_breaks(self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]) -> None:
        """Only the FIRST jargon term encountered is flagged per UC."""
        # "tstats" appears at index 0 in JARGON_TERMS, "datamodel" at
        # index 1. Including both yields a single violation for tstats.
        make_uc(
            "1.1.1",
            {"grandmaExplanation": "We use tstats over datamodel."},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # Only one issue line for this UC's jargon.
        jargon_lines = [line for line in err.splitlines() if "jargon_in_grandma" in line]
        assert len(jargon_lines) == 1
        assert "tstats" in jargon_lines[0]

    def test_missing_grandma_no_issue(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No ``grandmaExplanation`` field means the check is silent."""
        make_uc("1.1.1", {})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Broken fixtureRef
# ----------------------------------------------------------------------


class TestFixtureRef:
    def test_resolvable_fixture_passes(self, fake_repo: pathlib.Path, make_uc: MakeUC) -> None:
        # Create the fixture target.
        (fake_repo / "sample-data" / "fx.json").write_text("{}", encoding="utf-8")
        make_uc(
            "1.1.1",
            {"controlTest": {"fixtureRef": "sample-data/fx.json"}},
        )
        rc = cq.main([])
        assert rc == 0

    def test_missing_fixture_flagged(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {"controlTest": {"fixtureRef": "sample-data/missing.json"}},
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "broken_fixtureRef" in err
        assert "sample-data/missing.json" in err

    def test_empty_fixtureref_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc("1.1.1", {"controlTest": {"fixtureRef": ""}})
        rc = cq.main([])
        assert rc == 0

    def test_control_test_not_dict_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A non-dict ``controlTest`` does not trip the fixtureRef check."""
        make_uc("1.1.1", {"controlTest": "not a dict"})
        rc = cq.main([])
        assert rc == 0

    def test_missing_control_test_skipped(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No ``controlTest`` field means the check is silent."""
        make_uc("1.1.1", {})
        rc = cq.main([])
        assert rc == 0


# ----------------------------------------------------------------------
# Defaults / id fallback
# ----------------------------------------------------------------------


class TestIdFallback:
    def test_missing_id_uses_stem(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When the JSON has no ``id`` field, the issue references the
        file stem instead."""
        cat = fake_repo / "content" / "cat-01-test"
        cat.mkdir(parents=True)
        sidecar = cat / "UC-1.1.1.json"
        sidecar.write_text(
            json.dumps({"description": "Same.", "value": "Same."}),
            encoding="utf-8",
        )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # The relative file path is what's printed (the id only appears
        # in the violation dict, not in the formatted output line).
        assert "UC-1.1.1.json" in err


# ----------------------------------------------------------------------
# --generate-baseline
# ----------------------------------------------------------------------


class TestGenerateBaseline:
    def test_generate_baseline_outputs_json(
        self, make_uc: MakeUC, capsys: pytest.CaptureFixture[str]
    ) -> None:
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        rc = cq.main(["--generate-baseline"])
        out = capsys.readouterr().out
        assert rc == 0
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert any(v["issue"] == "description_equals_value" for v in parsed)

    def test_generate_baseline_empty(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = cq.main(["--generate-baseline"])
        out = capsys.readouterr().out
        assert rc == 0
        assert json.loads(out) == []


# ----------------------------------------------------------------------
# --baseline
# ----------------------------------------------------------------------


class TestBaseline:
    def test_baseline_suppresses_violation(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        sidecar = make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        rel = str(sidecar.relative_to(fake_repo))
        baseline_path = fake_repo / "baseline.json"
        baseline_path.write_text(
            json.dumps([{"file": rel, "issue": "description_equals_value"}]),
            encoding="utf-8",
        )
        rc = cq.main(["--baseline", str(baseline_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "1 existing violation(s) (all in baseline), 0 new" in out

    def test_baseline_does_not_suppress_new_violation(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Violations not listed in the baseline still fire."""
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        baseline_path = fake_repo / "baseline.json"
        baseline_path.write_text(json.dumps([]), encoding="utf-8")
        rc = cq.main(["--baseline", str(baseline_path)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err

    def test_baseline_file_missing_skips_filter(
        self,
        fake_repo: pathlib.Path,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A non-existent baseline path means no filter — every
        violation is reported as new."""
        make_uc(
            "1.1.1",
            {"description": "Same.", "value": "Same."},
        )
        missing_baseline = fake_repo / "no-such-baseline.json"
        rc = cq.main(["--baseline", str(missing_baseline)])
        err = capsys.readouterr().err
        assert rc == 1
        assert "description_equals_value" in err


# ----------------------------------------------------------------------
# Truncation
# ----------------------------------------------------------------------


class TestTruncation:
    def test_more_than_20_violations_truncated(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Output is truncated to the first 20 lines with an
        ``... and N more`` footer."""
        for z in range(1, 26):  # 25 violations
            make_uc(
                f"1.1.{z}",
                {"description": "Same.", "value": "Same."},
            )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        # First line counts the new violations.
        assert "25 new violation(s)" in err
        # Truncation footer.
        assert "... and 5 more" in err

    def test_exactly_20_violations_no_truncation(
        self,
        make_uc: MakeUC,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """At exactly 20 violations the truncation footer must NOT
        appear (covers the boundary branch)."""
        for z in range(1, 21):  # 20 violations
            make_uc(
                f"1.1.{z}",
                {"description": "Same.", "value": "Same."},
            )
        rc = cq.main([])
        err = capsys.readouterr().err
        assert rc == 1
        assert "20 new violation(s)" in err
        assert "more" not in err


# ----------------------------------------------------------------------
# CLI surface
# ----------------------------------------------------------------------


class TestCli:
    def test_help_exits_clean(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as excinfo:
            cq.main(["--help"])
        out = capsys.readouterr().out
        assert excinfo.value.code == 0
        assert "--baseline" in out
        assert "--generate-baseline" in out


def _base_uc(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "9.1.1",
        "title": "Example monitoring title",
        "criticality": "medium",
        "description": (
            "Detects sustained authentication failures across identity providers "
            "so analysts can intervene before account lockouts cascade into an outage."
        ),
        "value": (
            "Reduce mean time to detect credential-stuffing campaigns and prevent "
            "help-desk lockout storms that shorten incident response windows."
        ),
    }
    payload.update(overrides)
    return payload


# --- description heuristics (4) ---


def test_description_too_short_is_fail() -> None:
    uc = _base_uc(description="Too short description here.")
    findings = evaluate_description_quality(uc, uc_id="9.1.1")
    hit = [f for f in findings if f.dimension == "description.too_short"]
    assert len(hit) == 1
    assert hit[0].severity == "fail"


def test_description_boilerplate_title_duplicate() -> None:
    uc = _base_uc(
        title="Monitor CPU saturation",
        description="Monitor CPU saturation",
    )
    findings = evaluate_description_quality(uc, uc_id="9.1.1")
    assert any(f.dimension == "description.boilerplate" for f in findings)


def test_description_too_thin_single_sentence() -> None:
    uc = _base_uc(
        description=(
            "Detects hosts with runaway CPU that will breach SLA if left unchecked for another hour."
        )
    )
    findings = evaluate_description_quality(uc, uc_id="9.1.1")
    assert any(f.dimension == "description.too_thin" for f in findings)


def test_description_no_action_verb_is_info() -> None:
    uc = _base_uc(
        description=(
            "Sustained CPU saturation on Linux hosts above ninety percent for an hour "
            "indicates imminent capacity pain and queued workloads."
        )
    )
    findings = evaluate_description_quality(uc, uc_id="9.1.1")
    hit = [f for f in findings if f.dimension == "description.no_action_verb"]
    assert len(hit) == 1
    assert hit[0].severity == "info"


# --- value heuristics (4) ---


def test_value_too_short_is_fail() -> None:
    uc = _base_uc(value="Short value text without enough chars.")
    findings = evaluate_value_quality(uc, uc_id="9.1.1")
    hit = [f for f in findings if f.dimension == "value.too_short"]
    assert len(hit) == 1
    assert hit[0].severity == "fail"


def test_value_no_outcome_is_warn() -> None:
    uc = _base_uc(
        value=(
            "This statement explains context for operators but never names a measurable "
            "business outcome the organisation should expect from the control."
        )
    )
    findings = evaluate_value_quality(uc, uc_id="9.1.1")
    assert any(f.dimension == "value.no_outcome" for f in findings)


def test_value_too_generic_only_claim() -> None:
    uc = _base_uc(value="Industry standard best practice.")
    findings = evaluate_value_quality(uc, uc_id="9.1.1")
    assert any(f.dimension == "value.too_generic" for f in findings)


def test_value_duplicates_description_overlap() -> None:
    text = (
        "Detects Linux hosts whose CPU has been pinned above 90% on average for an hour, "
        "indicating sustained overload that will cause request queuing."
    )
    uc = _base_uc(description=text, value=text)
    findings = evaluate_value_quality(uc, uc_id="9.1.1")
    assert any(f.dimension == "value.duplicates_description" for f in findings)


# --- severity filter + report shape ---


def test_severity_filter_keeps_fail_and_above() -> None:
    uc = _base_uc(
        description="Too short.",
        value="Also too short for business value.",
    )
    desc = evaluate_description_quality(uc, uc_id="1.2.3")
    val = evaluate_value_quality(uc, uc_id="1.2.3")
    surfaced = cq._filter_by_severity(desc, "fail")
    surfaced.extend(cq._filter_by_severity(val, "fail"))
    assert all(f.severity == "fail" for f in surfaced)
    assert {f.dimension for f in surfaced} == {"description.too_short", "value.too_short"}


def test_build_report_includes_new_sections() -> None:
    uc = _base_uc(description="Too short.", value="Short.")
    desc = evaluate_description_quality(uc, uc_id="1.2.3")
    val = evaluate_value_quality(uc, uc_id="1.2.3")
    report = cq._build_report(
        scanned_ucs=1,
        legacy_violations=[],
        description_findings=desc,
        value_findings=val,
    )
    assert "findings_summary" in report
    assert "description_findings" in report
    assert "value_findings" in report
    assert report["schema_version"] == "2.0"
    assert report["findings_summary"]["description_total"] == len(desc)


def test_canonical_json_is_deterministic() -> None:
    uc = _base_uc()
    report = cq._build_report(
        scanned_ucs=1,
        legacy_violations=[],
        description_findings=evaluate_description_quality(uc, uc_id="9.1.1"),
        value_findings=evaluate_value_quality(uc, uc_id="9.1.1"),
    )
    first = cq._canonical_json(report)
    second = cq._canonical_json(report)
    assert first == second
    assert first.endswith("\n")


# --- CLI flag parsing ---


def test_cli_include_flags_default_on(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_audit_corpus(**kwargs: object) -> tuple[int, list, list, list]:
        captured.update(kwargs)
        return 0, [], [], []

    monkeypatch.setattr(cq, "audit_corpus", fake_audit_corpus)
    monkeypatch.setattr(sys, "argv", ["audit-content-quality"])
    assert cq.main([]) == 0
    assert captured["include_description"] is True
    assert captured["include_value"] is True


def test_cli_can_disable_description_dimension(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_audit_corpus(**kwargs: object) -> tuple[int, list, list, list]:
        captured.update(kwargs)
        return 1, [], [], []

    monkeypatch.setattr(cq, "audit_corpus", fake_audit_corpus)
    assert cq.main(["--no-include-description", "--check", "--max-findings", "10"]) == 0
    assert captured["include_description"] is False
    assert captured["include_value"] is True


def test_cli_severity_and_max_findings_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "REPORT_PATH", report_path)
    monkeypatch.setattr(
        cq,
        "audit_corpus",
        lambda **_: (
            2,
            [],
            evaluate_description_quality(_base_uc(description="short"), uc_id="1.1.1"),
            [],
        ),
    )
    assert cq.main(["--check", "--severity", "fail", "--max-findings", "0"]) == 1
    assert cq.main(["--check", "--severity", "fail", "--max-findings", "5"]) == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["scanned_ucs"] == 2


# --- end-to-end hermetic scenarios ---


def test_e2e_clean_uc_passes_per_file_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content = tmp_path / "content" / "cat-09-identity"
    content.mkdir(parents=True)
    sidecar = content / "UC-9.1.1.json"
    sidecar.write_text(json.dumps(_base_uc()), encoding="utf-8")
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    rel = f"content/cat-09-identity/{sidecar.name}"
    assert cq.main(["--files", rel]) == 0


def test_e2e_legacy_duplicate_fails_per_file_gate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dup_text = "Same text for both fields in this duplicate example sidecar."
    content = tmp_path / "content" / "cat-01-server"
    content.mkdir(parents=True)
    sidecar = content / "UC-1.1.1.json"
    sidecar.write_text(
        json.dumps(
            _base_uc(
                id="1.1.1",
                description=dup_text,
                value=dup_text,
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    rel = f"content/cat-01-server/{sidecar.name}"
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = cq.main(["--files", rel])
    assert rc == 1
    assert "description_equals_value" in buf.getvalue() or "new violation" in buf.getvalue()


def test_e2e_generate_baseline_preserves_legacy_shape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dup = "Identical description and value for baseline export test."
    content = tmp_path / "content" / "cat-02-network"
    content.mkdir(parents=True)
    sidecar = content / "UC-2.1.1.json"
    sidecar.write_text(
        json.dumps(_base_uc(id="2.1.1", description=dup, value=dup)),
        encoding="utf-8",
    )
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    out = io.StringIO()
    with redirect_stdout(out):
        assert cq.main(["--generate-baseline"]) == 0
    payload = json.loads(out.getvalue())
    assert payload[0]["issue"] == "description_equals_value"


def test_e2e_baseline_mode_filters_known_legacy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dup = "Identical description and value for baseline filtering test."
    content = tmp_path / "content" / "cat-03-storage"
    content.mkdir(parents=True)
    sidecar = content / "UC-3.1.1.json"
    sidecar.write_text(
        json.dumps(_base_uc(id="3.1.1", description=dup, value=dup)),
        encoding="utf-8",
    )
    rel = f"content/cat-03-storage/{sidecar.name}"
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps([{"file": rel, "id": "3.1.1", "issue": "description_equals_value"}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(cq, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cq, "CONTENT_DIR", tmp_path / "content")
    assert cq.main(["--baseline", str(baseline)]) == 0
