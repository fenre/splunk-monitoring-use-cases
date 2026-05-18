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

from splunk_uc.audits import gold_profile  # noqa: E402
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
    for fname in ("description", "value", "dataSources", "detailedImplementation"):
        assert fname in report.failing_fields
        messages = report.failing_fields[fname]
        assert isinstance(messages, list)
        assert messages


def test_to_json_returns_dict_with_expected_keys() -> None:
    report = GapReport(
        uc_id="15.1.1",
        sidecar_path=Path("/tmp/UC-15.1.1.json"),
        target_tier=TargetTier.SILVER,
        current_score=42,
        failing_fields={"description": ["too short"]},
    )
    payload = report.to_json()
    assert payload["uc_id"] == "15.1.1"
    assert payload["sidecar_path"] == "/tmp/UC-15.1.1.json"
    assert payload["target_tier"] == "silver"
    assert payload["current_score"] == 42
    assert payload["failing_fields"] == {"description": ["too short"]}


def test_load_sidecar_rejects_non_object_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("[1, 2, 3]")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_sidecar(bad)


def test_load_sidecar_tolerates_utf8_bom(tmp_path: Path) -> None:
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_bytes("\ufeff".encode("utf-8") + b'{"id": "15.1.1"}')
    assert load_sidecar(sidecar) == {"id": "15.1.1"}


def test_resolve_sidecar_path_raises_on_duplicate_match(tmp_path: Path) -> None:
    cat_a = tmp_path / "content" / "cat-15-x"
    cat_b = tmp_path / "content" / "cat-15-y"
    cat_a.mkdir(parents=True)
    cat_b.mkdir(parents=True)
    (cat_a / "UC-15.1.1.json").write_text("{}")
    (cat_b / "UC-15.1.1.json").write_text("{}")
    with pytest.raises(RuntimeError, match="multiple sidecars"):
        resolve_sidecar_path("UC-15.1.1", content_root=tmp_path / "content")


def test_score_uc_collects_multiple_gaps_per_field_as_list(tmp_path: Path) -> None:
    """A field that fails at both Silver and Gold thresholds appears as a list."""

    detailed = (
        "x" * 250 + "\nPrerequisites here\nStep 1 configure data\nStep 2 search\nStep 3 validate"
    )
    sidecar_data = {
        "id": "15.1.1",
        "title": "Test",
        "description": "x" * 50,
        "value": "x" * 50,
        "dataSources": "x" * 50,
        "implementation": "i" * 25,
        "detailedImplementation": detailed,
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
        "equipment": [],
        "grandmaExplanation": "g" * 25,
        "wave": "crawl",
        "prerequisiteUseCases": [],
        "visualization": "stub visualization text here ok",
        "equipmentModels": [],
    }
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps(sidecar_data))
    report = score_uc(sidecar, target_tier=TargetTier.SILVER)
    desc_gaps = report.failing_fields.get("description", [])
    assert isinstance(desc_gaps, list)
    assert len(desc_gaps) >= 2, (
        f"expected at least 2 gaps for description (Silver + Gold), got {desc_gaps!r}"
    )
    assert any("Silver" in g for g in desc_gaps)
    assert any("Gold" in g for g in desc_gaps)


def test_score_sidecar_facade_matches_audit_uc_depth() -> None:
    """Facade drift guard: score_sidecar depth_score equals audit_uc's."""

    sample = {
        "id": "15.1.1",
        "title": "Drift guard",
        "description": "x" * 50,
        "value": "x" * 50,
        "dataSources": "x" * 50,
        "implementation": "stub-longer-text-here",
        "detailedImplementation": "x" * 100,
        "knownFalsePositives": [],
        "references": [],
        "controlTest": {"positiveScenario": "a", "negativeScenario": "a"},
        "evidence": "",
        "exclusions": "",
        "splunkPillar": "platform",
        "spl": "search index=main",
        "monitoringType": "trend",
        "criticality": 50,
        "difficulty": "medium",
        "app": "splunk_app",
    }
    fake = gold_profile.REPO_ROOT / "content" / "scoring-only.json"
    direct = gold_profile.audit_uc(sample, fake)
    facade_score, _ = gold_profile.score_sidecar(sample)
    assert facade_score == direct["depth_score"]


def test_score_uc_normalises_reference_singular_to_plural(tmp_path: Path) -> None:
    """The 'reference' -> 'references' singular-to-plural mapping is observable."""

    detailed = (
        "x" * 250 + "\nPrerequisites here\nStep 1 configure data\nStep 2 search\nStep 3 validate"
    )
    sidecar_data = {
        "id": "15.1.1",
        "title": "Test",
        "description": "x" * 80,
        "value": "y" * 80,
        "dataSources": "x" * 60,
        "implementation": "stub-implementation-text",
        "detailedImplementation": detailed,
        "knownFalsePositives": [],
        "references": [],
        "controlTest": {"positiveScenario": "a", "negativeScenario": "a"},
        "evidence": "",
        "exclusions": "",
        "splunkPillar": "platform",
        "spl": "search index=main",
        "monitoringType": "trend",
        "criticality": 50,
        "difficulty": "medium",
        "app": "splunk_app",
        "grandmaExplanation": "in plain language here ok",
        "wave": "crawl",
        "prerequisiteUseCases": [],
        "equipment": [],
        "visualization": "stub visualization text here ok",
        "equipmentModels": [],
    }
    sidecar = tmp_path / "UC-15.1.1.json"
    sidecar.write_text(json.dumps(sidecar_data))
    report = score_uc(sidecar, target_tier=TargetTier.SILVER)
    assert "references" in report.failing_fields
    assert "reference" not in report.failing_fields
