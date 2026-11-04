"""Tests for template fingerprint detection and audit-template-provenance."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.audits import template_provenance  # noqa: E402
from splunk_uc.audits._template_fingerprints import (  # noqa: E402
    detect_template_flags,
    is_fully_templated_v2,
)


def test_detect_full_v2_template_flags() -> None:
    uc = {
        "knownFalsePositives": "1. **Scheduled maintenance windows** — CMDB\n**Suppression mechanism:** operational_exceptions.csv",
        "controlTest": {
            "positiveScenario": "On a lab host or staging index, ingest sample events",
            "negativeScenario": "entities listed in operational_exceptions.csv",
        },
        "exclusions": "Does not replace enterprise SIEM correlation for unrelated threat classes.",
        "evidence": "Saved search uc_1_1_1_foo, dashboard panel tied to this UC, weekly CSV export archived to index=evidence",
    }
    flags = detect_template_flags(uc)
    assert is_fully_templated_v2(flags)
    assert "generic_kfp" in flags
    assert "generic_controlTest" in flags


def test_clean_uc_has_no_flags() -> None:
    uc = {
        "knownFalsePositives": "Strava OAuth refresh failure mimics missing data.",
        "controlTest": {
            "positiveScenario": "Ingest strava:activity rows above goal_km threshold.",
            "negativeScenario": "Rest week with zero runs — expect zero alert rows.",
        },
        "exclusions": "Personal fitness tracking only; not enterprise security monitoring.",
        "evidence": "Saved search strava_weekly_goal in index=personal dashboard.",
    }
    flags = detect_template_flags(uc)
    assert flags == []


def test_audit_template_provenance_on_real_exemplar(tmp_path: Path) -> None:
    exemplar = REPO_ROOT / "content" / "cat-25-personal-hobbyist-monitoring" / "UC-25.1.1.json"
    if not exemplar.is_file():
        return
    payload = template_provenance.audit_paths([exemplar])
    assert payload["summary"]["total"] == 1
    assert payload["summary"]["any_template"] == 0
    assert payload["summary"]["clean"] == 1


def test_audit_paths_empty_flags_not_listed(tmp_path: Path) -> None:
    sidecar = {
        "id": "99.1.1",
        "knownFalsePositives": "Vendor-specific scenario only.",
        "controlTest": {"positiveScenario": "a", "negativeScenario": "b" * 40},
        "exclusions": "Scope limited to hobby project.",
        "evidence": "Personal dashboard panel.",
    }
    path = tmp_path / "UC-99.1.1.json"
    path.write_text(json.dumps(sidecar))
    payload = template_provenance.audit_paths([path])
    assert payload["summary"]["clean"] == 1
    assert payload["ucs"] == []


def test_audit_paths_reports_v2_families_separately(tmp_path: Path) -> None:
    sidecar = {
        "id": "99.1.2",
        "description": "Detects UC-99.1.2 — Foo, Bar, Baz — using index=main.",
        "value": "Tracking `x` via UC-99.1.2 on `y` feeds improves response.",
        "evidence": "Saved search `ops_foo` (UC-99.1.2), SOC dashboard panel \"Ops\".",
    }
    path = tmp_path / "UC-99.1.2.json"
    path.write_text(json.dumps(sidecar))
    payload = template_provenance.audit_paths([path])
    summary = payload["summary"]
    assert summary["any_template"] == 0
    assert summary["any_template_v2_families"] == 1
    assert summary["by_flag_v2_families"] == {
        "v2_description_selfref": 1,
        "v2_description_title_salad": 1,
        "v2_evidence_skeleton": 1,
        "v2_value_selfref": 1,
    }


def test_max_any_v2_cap(tmp_path: Path, monkeypatch) -> None:
    sidecar = {"id": "99.1.3", "value": "UC-99.1.3 operationalises 'x' against `y` feeds."}
    path = tmp_path / "UC-99.1.3.json"
    path.write_text(json.dumps(sidecar))
    monkeypatch.setattr(template_provenance, "REPORT_PATH", tmp_path / "report.json")
    monkeypatch.setattr(template_provenance, "REPO_ROOT", tmp_path)
    assert template_provenance.main(["--files", str(path), "--check", "--max-any-v2", "0"]) == 1
    assert template_provenance.main(["--files", str(path), "--check", "--max-any-v2", "1"]) == 0
