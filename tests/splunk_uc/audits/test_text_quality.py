"""Tests for the deterministic UC text-quality pre-pass (audit-text-quality)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.audits import text_quality as tq  # noqa: E402
from splunk_uc.audits._template_fingerprints import (  # noqa: E402
    V2_FAMILIES,
    detect_template_flags_v2,
    v2_flags_in_fields,
)
from splunk_uc.review._ledger import validate_record  # noqa: E402


def _generated_uc() -> dict[str, object]:
    return {
        "id": "5.1.1",
        "title": "Interface Up/Down Events",
        "splunkPillar": "Observability",
        "description": (
            "Detects UC-5.1.1 — Interface, Down, Events — using `index=network`. "
            "Purpose-built for 'Interface Up/Down Events' in Operations workflows."
        ),
        "value": "Tracking `activity` via UC-5.1.1 on `cisco:ios` feeds improves response.",
        "controlTest": {
            "positiveScenario": "UC-5.1.1 positive (Interface, Down, Events): ingest synthetic events.",
            "negativeScenario": "UC-5.1.1 negative (Up/Down Events): benign. Variant 12 confirms zero alert rows.",
        },
        "knownFalsePositives": (
            "1. **Maintenance window on `network` (UC-5.1.1)** — planned work.\n"
            "**Suppression mechanism:** `ops_exception_register.csv`"
        ),
        "evidence": "Saved search `operations_interface_up_down_events` (UC-5.1.1), SOC dashboard panel.",
        "exclusions": "Covers the detection logic documented for 'Interface Up/Down Events' only.",
        "references": [{"title": "Lantern", "url": "https://lantern.splunk.com/"}],
        "app": "`TA-cisco_ios` — Splunk Add-on for Cisco Security (Splunkbase 1352)",
        "premiumApps": [{"name": "Splunk User Behavior Analytics"}],
        "cimModels": [],
        "cimSpl": "| tstats count from datamodel=Network_Traffic.All_Traffic by All_Traffic.dvc",
    }


def _clean_uc() -> dict[str, object]:
    return {
        "id": "25.1.1",
        "title": "Strava Weekly Distance vs Goal",
        "splunkPillar": "Observability",
        "description": "Compares weekly Strava running distance against a personal goal and flags short weeks.",
        "value": "Keeps a training plan honest by surfacing missed weekly targets before a race block slips.",
        "controlTest": {
            "positiveScenario": "Ingest three strava:activity runs totalling 12 km against a 30 km goal; expect one row.",
            "negativeScenario": "Ingest runs totalling 32 km; expect zero rows.",
        },
        "knownFalsePositives": "1. **Rest week** — planned taper weeks fall below goal by design.",
        "evidence": "Saved search strava_weekly_goal in index=personal.",
        "exclusions": "Personal fitness tracking only.",
        "references": [
            {"title": "Strava API", "url": "https://developers.strava.com/docs/reference/"}
        ],
        "app": "Splunk Add-on for Amazon Web Services (Splunkbase 1876)",
        "cimModels": [],
        "cimSpl": "",
    }


def test_v2_families_detect_every_generated_pattern() -> None:
    flags = set(detect_template_flags_v2(_generated_uc()))
    assert flags == set(V2_FAMILIES)


def test_v2_families_clean_uc_has_no_flags() -> None:
    assert detect_template_flags_v2(_clean_uc()) == []


def test_v2_flags_in_fields_scopes_to_lifted_fields() -> None:
    flags = detect_template_flags_v2(_generated_uc())
    scoped = v2_flags_in_fields(flags, {"evidence", "value"})
    assert scoped == ["v2_evidence_skeleton", "v2_value_selfref"]


def test_review_uc_flags_correctness_checks() -> None:
    record = tq.review_uc(
        REPO_ROOT / "content" / "cat-05-network-infrastructure" / "UC-5.1.1.json",
        _generated_uc(),
        skeleton_index=None,
        min_cluster=50,
        spelling={},
    )
    checks = {f["check"] for f in record["findings"]}
    assert "premium_app_pillar_mismatch" in checks
    assert "cim_models_missing" in checks
    assert "splunkbase_name_mismatch" in checks
    assert validate_record(record) == []


def test_review_uc_clean_record_is_valid_and_empty() -> None:
    record = tq.review_uc(
        REPO_ROOT / "content" / "cat-25-personal-hobbyist-monitoring" / "UC-25.1.1.json",
        _clean_uc(),
        skeleton_index=None,
        min_cluster=50,
        spelling={},
    )
    assert record["findings"] == []
    assert record["firewalled_field_flags"] == []
    assert validate_record(record) == []


def test_template_quote_is_the_offending_sentence() -> None:
    findings = tq.check_templates(_generated_uc())
    purpose = next(f for f in findings if f["check"].endswith("purpose_built"))
    assert purpose["quote"].startswith("Purpose-built for")
    variant = next(f for f in findings if f["check"].endswith("controlTest_variant"))
    assert "Variant 12 confirms" in variant["quote"]


def test_sentence_skeleton_collides_generated_siblings() -> None:
    a = tq.sentence_skeleton(
        "Tracking `bytes` via UC-1.2.3 on `aws:s3` feeds improves response to 'X'."
    )
    b = tq.sentence_skeleton(
        "Tracking `errors` via UC-9.9.9 on `cisco:asa` feeds improves response to 'Y'."
    )
    assert a and a == b


def test_skeleton_cluster_threshold() -> None:
    uc = {
        "id": "1.1.1",
        "value": "Tracking `x` via UC-1.1.1 on `y` feeds improves response to 'z' today.",
    }
    skeleton = tq.sentence_skeleton(uc["value"])
    index = {field: Counter() for field in tq.CLUSTER_FIELDS}
    index["value"][skeleton] = 60
    hits = tq.check_skeleton_clusters(uc, index, min_cluster=50, skip_fields=set())
    assert [f["check"] for f in hits] == ["skeleton_cluster:value"]
    assert tq.check_skeleton_clusters(uc, index, min_cluster=61, skip_fields=set()) == []
    assert tq.check_skeleton_clusters(uc, index, min_cluster=50, skip_fields={"value"}) == []


def test_title_token_salad_requires_title_words() -> None:
    uc = {
        "title": "Salesforce API Access Volume Anomalies",
        "controlTest": {
            "positiveScenario": "Run (Salesforce, API, Access, Volume) now.",
            "negativeScenario": "",
        },
        "description": "Uses Okta, Duo, Ping for MFA.",
    }
    hits = tq.check_title_token_salad(uc, skip_fields=set())
    assert [f["field"] for f in hits] == ["controlTest"]


def test_premium_app_allowed_on_security_pillar() -> None:
    uc = {"splunkPillar": "Security", "premiumApps": [{"name": "Splunk Enterprise Security"}]}
    assert tq.check_premium_apps(uc) == []


@pytest.mark.parametrize(
    ("cim_models", "expected"),
    [
        ([], {"cim_models_missing"}),
        (["Authentication"], {"cim_models_mismatch"}),
        (["Network_Traffic.All_Traffic"], set()),
        (["Network Traffic"], set()),
        (["Vulnerabilities (when Tenable"], {"cim_models_malformed"}),
    ],
)
def test_cim_checks(cim_models: list[str], expected: set[str]) -> None:
    uc = {"cimModels": cim_models, "cimSpl": "| tstats count from datamodel=Network_Traffic by x"}
    assert {f["check"] for f in tq.check_cim(uc)} == expected


def test_splunkbase_name_overlap() -> None:
    listing = {"displayName": "Splunk Operational Technology Intelligence (OTI)", "name": "OTI"}
    assert tq.splunkbase_name_overlap("Splunk OT Intelligence", listing) == 1.0
    aws = {"displayName": "Splunk Add-on for Amazon Web Services (AWS)", "name": "Splunk_TA_aws"}
    assert tq.splunkbase_name_overlap("collected via Splunk Add-on for AWS", aws) == 1.0
    pure = {"displayName": "PureStorage Unified Add-on for Splunk", "name": "x"}
    assert tq.splunkbase_name_overlap("Pure Storage Unified Add-on for Splunk", pure) == 1.0
    cisco = {"displayName": "App for Cisco Network Data", "name": "cisco_ios"}
    overlap = tq.splunkbase_name_overlap("Splunk Add-on for Cisco Security", cisco)
    assert overlap is not None and overlap < tq.NAME_MATCH_MIN


def test_mention_segment_strips_connectors_and_verbs() -> None:
    assert tq.mention_segment("1108 collected by Splunk Add-on for Microsoft Windows") == (
        "Splunk Add-on for Microsoft Windows"
    )
    assert (
        tq.mention_segment("Install Splunk Add-on for ServiceNow") == "Splunk Add-on for ServiceNow"
    )


def test_splunkbase_unknown_id_is_needs_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tq, "load_splunkbase_catalog", lambda: {"1876": {"displayName": "AWS"}})
    hits = tq.check_splunkbase({"app": "Universal Forwarder (Splunkbase 617)"})
    assert [(f["check"], f["severity"]) for f in hits] == [
        ("splunkbase_unknown_id", "needs_verification")
    ]


def test_duplicate_prose() -> None:
    text = (
        "Alerts when the Cisco interface flaps more than three times in ten minutes on any uplink."
    )
    hits = tq.check_duplicate_prose({"description": text, "value": text + " Really."})
    assert [f["severity"] for f in hits] == ["major"]


def test_spelling_ignores_code_contractions_and_allowlist() -> None:
    dictionary = {"seperately": "separately", "couldn": "could"}
    uc = {
        "description": "Run each check seperately; it couldn't run `seperately` in code.",
        "value": "",
    }
    hits = tq.check_spelling(uc, dictionary)
    assert len(hits) == 1
    assert hits[0]["quote"] == "seperately"


def test_placeholder_title_and_sourcetype_are_firewalled_flags() -> None:
    uc = {
        "title": "Prep Metric1 Weekend vs Weekday Split",
        "spl": 'index=personal sourcetype="prep:metric1"',
    }
    flags = tq.check_placeholders(uc)
    assert [f["field"] for f in flags] == ["title", "spl"]


def test_main_writes_ledger_and_summary(tmp_path: Path) -> None:
    uc_path = REPO_ROOT / "content" / "cat-05-network-infrastructure" / "UC-5.1.1.json"
    out = tmp_path / "ledger.jsonl"
    summary = tmp_path / "summary.json"
    rc = tq.main(
        [
            "--files",
            str(uc_path),
            "--no-clusters",
            "--no-spelling",
            "--out",
            str(out),
            "--summary",
            str(summary),
        ]
    )
    assert rc == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["uc_id"] == "UC-5.1.1"
    assert validate_record(record) == []
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["ucs"] == 1


def test_main_check_caps(tmp_path: Path) -> None:
    uc_path = REPO_ROOT / "content" / "cat-05-network-infrastructure" / "UC-5.1.1.json"
    rc = tq.main(
        ["--files", str(uc_path), "--no-clusters", "--no-write", "--check", "--max-major", "0"]
    )
    assert rc == 1
