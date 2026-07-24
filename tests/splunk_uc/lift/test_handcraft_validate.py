"""Tests for lift-validate --require-handcraft anti-lazy gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import validate  # noqa: E402
from splunk_uc.tools.lift._handcraft import validate_handcraft  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _templated_uc() -> dict[str, object]:
    return {
        "id": "25.1.1",
        "title": "Strava Weekly Distance vs Goal",
        "spl": "index=personal sourcetype=strava:activity",
        "dataSources": "Strava API strava:activity via HEC",
        "app": "Splunk HEC Splunkbase 617",
        "knownFalsePositives": (
            "1. **Scheduled maintenance windows** — CMDB\n"
            "**Suppression mechanism:** operational_exceptions.csv"
        ),
        "controlTest": {
            "positiveScenario": "On a lab host or staging index, ingest sample events",
            "negativeScenario": "operational_exceptions.csv",
        },
        "exclusions": "Does not replace enterprise SIEM correlation.",
        "evidence": (
            "Saved search uc_25_1_1_strava, dashboard panel tied to this UC, "
            "weekly CSV export archived to index=evidence"
        ),
        "description": "Original description.",
        "value": "Original value statement.",
        "detailedImplementation": "Step 1\nStep 2",
    }


def _handcrafted_lifted(original: dict[str, object]) -> dict[str, object]:
    lifted = dict(original)
    lifted["knownFalsePositives"] = (
        "1. **OAuth token expiry** — Strava API returns 401; connector stops but old strava:activity rows remain.\n"
        "2. **Rest week** — zero runs is expected; distinguish from ingestion failure via vendor app.\n"
        "3. **Double sync** — watch and phone both post the same activity_id.\n"
        "4. **UTC weekly bins** — local-time athletes misaligned with `span=1w`.\n"
        "**Suppression:** dedup by external_id in SPL; no enterprise exception register."
    )
    lifted["controlTest"] = {
        "positiveScenario": (
            "Ingest strava:activity rows into index=personal with distance_km above goal_km; "
            "saved search returns behind status."
        ),
        "negativeScenario": (
            "Ingest compliant strava:activity rows under goal_km for the week; expect zero alert rows."
        ),
    }
    lifted["exclusions"] = (
        "Personal fitness tracking only; does not attest to enterprise security or regulatory compliance."
    )
    lifted["evidence"] = (
        "Saved search strava_weekly_goal in index=personal; dashboard panel UC-25.1.1 weekly km chart."
    )
    lifted["detailedImplementation"] = (
        "Prerequisites\n• HEC token on index=personal\n• Strava OAuth refresh\n\n"
        "Step 1 — Configure strava:activity collection via HEC.\n"
        "Step 2 — Schedule SPL over index=personal sourcetype=strava:activity.\n"
        "Step 3 — Validate totals against Strava app You tab.\n"
        "Step 4 — Dashboard with weekly km vs goal_km.\n"
        "Step 5 — Troubleshoot OAuth 401, NULL distance_km, UTC bucket drift, duplicate activity_id."
    )
    lifted["description"] = (
        "Compares weekly Strava running distance in index=personal against a personal goal_km target."
    )
    lifted["value"] = (
        "Turns vague training intent into a concrete weekly score so you adjust volume before missing the goal."
    )
    return lifted


def test_validate_handcraft_rejects_remaining_templates() -> None:
    original = _templated_uc()
    lifted = dict(original)
    lifted["description"] = "Still templated KFP below."
    reasons = validate_handcraft(
        original=original,
        lifted=lifted,
        lifted_field_names={"description"},
    )
    assert any("template provenance" in r for r in reasons)


def test_validate_handcraft_accepts_domain_specific_lift() -> None:
    original = _templated_uc()
    lifted = _handcrafted_lifted(original)
    reasons = validate_handcraft(
        original=original,
        lifted=lifted,
        lifted_field_names={
            "knownFalsePositives",
            "controlTest",
            "exclusions",
            "evidence",
            "detailedImplementation",
            "description",
            "value",
        },
    )
    assert reasons == []


def test_lift_validate_refuses_lazy_diff(tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-25-personal-hobbyist-monitoring"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-25.1.1.json"
    original = _templated_uc()
    sidecar.write_text(json.dumps(original))

    diff_path = tmp_path / "lift.diff.json"
    diff_path.write_text(
        json.dumps(
            {
                "uc_id": "25.1.1",
                "target_tier": "silver",
                "lifted_fields": {
                    "description": "A slightly longer description that still leaves templates.",
                },
            }
        )
    )
    exit_code = validate.main(
        [
            "UC-25.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(tmp_path / "content"),
            "--require-handcraft",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    after = json.loads(sidecar.read_text())
    assert after["description"] == original["description"]


def test_lift_validate_accepts_handcraft_diff(tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-25-personal-hobbyist-monitoring"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-25.1.1.json"
    original = _templated_uc()
    sidecar.write_text(json.dumps(original))

    lifted = _handcrafted_lifted(original)
    diff_path = tmp_path / "lift.diff.json"
    diff_path.write_text(
        json.dumps(
            {
                "uc_id": "25.1.1",
                "target_tier": "silver",
                "lifted_fields": {
                    k: lifted[k]
                    for k in (
                        "knownFalsePositives",
                        "controlTest",
                        "exclusions",
                        "evidence",
                        "detailedImplementation",
                        "description",
                        "value",
                        "dataSources",
                    )
                },
            }
        )
    )
    exit_code = validate.main(
        [
            "UC-25.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(tmp_path / "content"),
            "--require-handcraft",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    after = json.loads(sidecar.read_text())
    assert "operational_exceptions.csv" not in after.get("knownFalsePositives", "")
