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
    assert payload["summary"]["any_template"] >= 1


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
