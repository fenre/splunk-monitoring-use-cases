"""Unit tests for the B-6 description / value dimension heuristics.

This file exists alongside ``test_content_quality.py`` (which P16 wave GG
expanded on ``main`` to cover the legacy ``content_quality`` audit core)
to keep the two test universes structurally separate during the B-6 →
``main`` rebase. The B-6 PR introduces:

* ``_content_quality_dimensions`` — a sibling module that scores
  ``description`` and ``value`` text against per-dimension heuristics
  (too-short, single-sentence, missing-action-verb, generic claim, etc.).
* New CLI flags on ``content_quality.main`` — ``--check`` /
  ``--report`` / ``--severity`` / ``--max-findings`` /
  ``--no-{description,value}-quality`` — that surface those dimensions
  for Lane N (handwritten content uplift).

The tests in this file pin **only** the new dimension behaviour. The
legacy core surface (jargon, exact-match, fixtureRef, ``--baseline`` /
``--generate-baseline``) is covered by ``test_content_quality.py``,
which was taken verbatim from ``main`` during the merge resolution.
There is no overlap between the two files.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from splunk_uc.audits import content_quality as cq
from splunk_uc.audits._content_quality_dimensions import (
    evaluate_description_quality,
    evaluate_value_quality,
)


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
