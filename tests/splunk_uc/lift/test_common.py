"""Tests for src/splunk_uc/tools/lift/_common.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift._common import (  # noqa: E402
    GapReport,
    TargetTier,
    load_sidecar,
    resolve_sidecar_path,
    score_uc,
)


def test_target_tier_parses_known_values() -> None:
    assert TargetTier.from_str("silver") is TargetTier.SILVER
    assert TargetTier.from_str("gold") is TargetTier.GOLD
    assert TargetTier.from_str("gold-v2") is TargetTier.GOLD_V2


def test_target_tier_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unknown tier"):
        TargetTier.from_str("platinum")


def test_resolve_sidecar_path_finds_existing_uc(tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    sidecar.write_text(json.dumps({"id": "15.1.1", "title": "x"}))
    assert resolve_sidecar_path("UC-15.1.1", content_root=tmp_path / "content") == sidecar


def test_resolve_sidecar_path_raises_for_unknown_uc(tmp_path: Path) -> None:
    (tmp_path / "content").mkdir()
    with pytest.raises(FileNotFoundError, match=r"UC-15\.1\.1"):
        resolve_sidecar_path("UC-15.1.1", content_root=tmp_path / "content")


def test_load_sidecar_returns_parsed_json(tmp_path: Path) -> None:
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps({"id": "15.1.1", "title": "test"}))
    assert load_sidecar(sidecar) == {"id": "15.1.1", "title": "test"}


def test_score_uc_returns_gap_report_for_short_fields(tmp_path: Path) -> None:
    sidecar_data = {
        "id": "15.1.1",
        "title": "Stub",
        "description": "d" * 45,
        "value": "v" * 45,
        "dataSources": "s" * 25,
        "detailedImplementation": "x" * 100,
        "knownFalsePositives": [],
        "references": ["https://a.example", "https://b.example"],
        "controlTest": {"positiveScenario": "a", "negativeScenario": "a"},
        "evidence": "",
        "exclusions": "",
        "splunkPillar": "platform",
        "spl": "search index=main",
        "monitoringType": "trend",
        "criticality": 50,
        "difficulty": "medium",
        "app": "splunk_app",
        "implementation": "i" * 25,
        "equipment": [],
        "grandmaExplanation": "g" * 25,
        "wave": "crawl",
        "prerequisiteUseCases": [],
        "visualization": "stub visualization text here",
        "equipmentModels": [],
    }
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps(sidecar_data))
    report = score_uc(sidecar, target_tier=TargetTier.SILVER)
    assert isinstance(report, GapReport)
    assert report.uc_id == "15.1.1"
    assert report.current_score < 50
    assert "description" in report.failing_fields
    assert "value" in report.failing_fields
    assert "dataSources" in report.failing_fields
    assert "detailedImplementation" in report.failing_fields
