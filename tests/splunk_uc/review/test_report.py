"""Tests for generate-uc-review-report."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.review import report  # noqa: E402
from splunk_uc.review._ledger import (  # noqa: E402
    SCORE_DIMENSIONS,
    content_sha256,
    record_path,
    write_record,
)

CAT = "cat-15-data-center-physical-infrastructure"


def _content(tmp_path: Path, *names: str) -> Path:
    root = tmp_path / "content"
    (root / CAT).mkdir(parents=True)
    for name in names:
        shutil.copy(REPO_ROOT / "content" / CAT / f"{name}.json", root / CAT / f"{name}.json")
    return root


def _record(
    uc_path: Path, tier: str, findings: list[dict], flags: list[dict], verdict: str
) -> dict:
    uc = json.loads(uc_path.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0",
        "uc_id": f"UC-{uc['id']}",
        "file": f"content/{CAT}/{uc_path.name}",
        "content_sha256": content_sha256(uc),
        "tier": tier,
        "model": f"model-{tier}",
        "rubric_version": "1.0",
        "verdict": verdict,
        "confidence": 0.8,
        "scores": dict.fromkeys(SCORE_DIMENSIONS, 3),
        "findings": findings,
        "firewalled_field_flags": flags,
    }


def test_build_prefers_deep_over_triage_and_ranks(tmp_path: Path) -> None:
    content = _content(tmp_path, "UC-15.1.1", "UC-15.1.2")
    ledger = tmp_path / "ledger"
    p1 = content / CAT / "UC-15.1.1.json"
    p2 = content / CAT / "UC-15.1.2.json"
    blocker = {
        "field": "dataSources",
        "dimension": "correctness",
        "severity": "blocker",
        "quote": "Universal Forwarder (Splunkbase 617)",
        "explanation": "617 is not a Splunkbase app.",
        "evidence_url": "https://splunkbase.splunk.com/app/617",
    }
    write_record(
        record_path("triage", CAT, "UC-15.1.1", root=ledger),
        _record(p1, "triage", [], [], "polish"),
    )
    write_record(
        record_path("deep", CAT, "UC-15.1.1", root=ledger),
        _record(
            p1,
            "deep",
            [blocker],
            [{"field": "spl", "issue": "timechart split twice", "severity": "major"}],
            "incorrect",
        ),
    )
    write_record(
        record_path("triage", CAT, "UC-15.1.2", root=ledger),
        _record(p2, "triage", [{**blocker, "severity": "major"}], [], "rewrite"),
    )
    summary, fix_queue = report.build(root=ledger, content_dir=content)

    assert summary["ucs_model_reviewed"] == 2
    assert summary["coverage"][CAT] == {
        "ucs": 2,
        "adjudication": 0,
        "deep": 1,
        "triage": 2,
        "stale": 0,
    }
    first, second = fix_queue["queue"]
    assert first["uc_id"] == "UC-15.1.1"
    assert first["tier"] == "deep"
    assert first["lanes"]["human"] == 1
    assert first["lanes"]["lift"] == 1
    assert first["score"] > second["score"]
    assert second["tier"] == "triage"


def test_recurring_blocker_quotes(tmp_path: Path) -> None:
    names = ["UC-15.1.1", "UC-15.1.2", "UC-15.1.3"]
    content = _content(tmp_path, *names)
    ledger = tmp_path / "ledger"
    blocker = {
        "field": "dataSources",
        "dimension": "correctness",
        "severity": "blocker",
        "quote": "Universal Forwarder (Splunkbase 617)",
        "explanation": "617 is not a Splunkbase app.",
        "evidence_url": "https://splunkbase.splunk.com/app/617",
    }
    for name in names:
        path = content / CAT / f"{name}.json"
        write_record(
            record_path("deep", CAT, name, root=ledger),
            _record(path, "deep", [blocker], [], "incorrect"),
        )
    summary, _ = report.build(root=ledger, content_dir=content)
    assert summary["recurring_blocker_quotes"][0]["ucs"] == 3


def test_stale_records_are_flagged(tmp_path: Path) -> None:
    content = _content(tmp_path, "UC-15.1.1")
    ledger = tmp_path / "ledger"
    path = content / CAT / "UC-15.1.1.json"
    record = _record(path, "deep", [], [], "polish")
    record["content_sha256"] = "0" * 64
    write_record(record_path("deep", CAT, "UC-15.1.1", root=ledger), record)
    summary, fix_queue = report.build(root=ledger, content_dir=content)
    assert summary["coverage"][CAT]["stale"] == 1
    assert fix_queue["queue"][0]["stale"] is True


def test_fix_lane() -> None:
    scripted = {"check": "template_v2:v2_controlTest_variant"}
    assert report.fix_lane(scripted, firewalled=False) == "scripted"
    assert report.fix_lane({"check": "premium_app_pillar_mismatch"}, firewalled=False) == "scripted"
    assert report.fix_lane({"check": "template_v2:v2_value_selfref"}, firewalled=False) == "lift"
    assert report.fix_lane({"check": "cim_models_missing"}, firewalled=False) == "lift"
    assert report.fix_lane({"field": "value"}, firewalled=False) == "lift"
    assert report.fix_lane({"field": "spl"}, firewalled=True) == "human"


def test_markdown_has_provenance_banner(tmp_path: Path) -> None:
    content = _content(tmp_path, "UC-15.1.1")
    summary, fix_queue = report.build(root=tmp_path / "empty", content_dir=content)
    text = report.render_markdown(summary, fix_queue)
    assert (
        "Generated by `python3 -m splunk_uc generate-uc-review-report`; do not hand-edit." in text
    )
    assert "0 of 1 UCs have at least one model review." in text


def test_human_lane_lists_firewalled_issues(tmp_path: Path) -> None:
    content = _content(tmp_path, "UC-15.1.1")
    ledger = tmp_path / "ledger"
    path = content / CAT / "UC-15.1.1.json"
    flag = {
        "field": "spl",
        "issue": "timechart accepts one split-by field",
        "severity": "blocker",
        "evidence_url": "https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Timechart",
    }
    write_record(
        record_path("deep", CAT, "UC-15.1.1", root=ledger),
        _record(path, "deep", [], [flag], "incorrect"),
    )
    _, fix_queue = report.build(root=ledger, content_dir=content)
    text = report.render_human_lane(fix_queue)
    assert f"## {CAT}" in text
    assert (
        "**spl** (blocker): timechart accepts one split-by field ([evidence](https://docs.splunk.com"
        in text
    )
