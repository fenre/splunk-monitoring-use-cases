"""Tests for the ``lift-prompt`` verb."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import prompt  # noqa: E402

FIREWALLED_FIELDS = (
    "spl",
    "cimSpl",
    "id",
    "title",
    "monitoringType",
    "splunkPillar",
    "criticality",
    "difficulty",
    "compliance",
    "fixtureRef",
    "assurance",
    "grandmaExplanation",
)
LIFT_SURFACE_FIELDS = (
    "description",
    "value",
    "dataSources",
    "detailedImplementation",
    "knownFalsePositives",
    "references",
    "controlTest",
    "evidence",
    "exclusions",
    "visualization",
    "equipmentModels",
    "mitreAttack",
)


def _stage_minimal_sidecar(tmp_path: Path) -> Path:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(
        json.dumps(
            {
                "id": "15.1.1",
                "title": "Test",
                "description": "short",
                "value": "short",
                "dataSources": "tiny",
                "spl": "search index=main",
                "detailedImplementation": "stub",
            }
        )
    )
    return tmp_path / "content"


def test_main_writes_prompt_with_required_sections(capsys, tmp_path: Path):
    content_root = _stage_minimal_sidecar(tmp_path)
    exit_code = prompt.main(["UC-15.1.1", "--content-root", str(content_root)])
    captured = capsys.readouterr()
    assert exit_code == 0
    text = captured.out
    assert "# RUBRIC" in text
    assert "# CURRENT UC SIDECAR" in text
    assert "# GAP REPORT" in text
    assert "# FIREWALL" in text
    assert "# OUTPUT SHAPE" in text
    for field in FIREWALLED_FIELDS:
        assert field in text, f"firewalled field {field!r} missing from prompt"
    for field in LIFT_SURFACE_FIELDS:
        assert field in text, f"lift-surface field {field!r} missing from prompt"
    assert "/tmp/lift-UC-15.1.1.diff.json" in text


def test_prompt_includes_loaded_sidecar_json(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar_data = {
        "id": "15.1.1",
        "title": "Cooling failure",
        "description": "Detect chiller failure",
        "value": "v",
        "dataSources": "bms",
        "spl": "search index=bms",
        "detailedImplementation": "stub",
    }
    (cat / "UC-15.1.1.json").write_text(json.dumps(sidecar_data))
    prompt.main(["UC-15.1.1", "--content-root", str(tmp_path / "content")])
    text = capsys.readouterr().out
    match = re.search(
        r"# CURRENT UC SIDECAR\s*\n```json\s*\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    assert match is not None
    assert json.loads(match.group(1))["id"] == "15.1.1"


def test_prompt_includes_gap_report_json(capsys, tmp_path: Path):
    content_root = _stage_minimal_sidecar(tmp_path)
    prompt.main(["UC-15.1.1", "--content-root", str(content_root)])
    text = capsys.readouterr().out
    match = re.search(
        r"# GAP REPORT\s*\n```json\s*\n(.*?)\n```",
        text,
        re.DOTALL,
    )
    assert match is not None
    payload = json.loads(match.group(1))
    assert payload["uc_id"] == "15.1.1"
    assert "current_score" in payload
    assert "failing_fields" in payload


def test_prompt_respects_target_tier_in_header(capsys, tmp_path: Path):
    content_root = _stage_minimal_sidecar(tmp_path)
    prompt.main(
        [
            "UC-15.1.1",
            "--target-tier",
            "gold",
            "--content-root",
            str(content_root),
        ]
    )
    text = capsys.readouterr().out
    assert "target tier: gold" in text.lower()


def test_main_returns_1_with_stderr_for_unknown_uc(capsys, tmp_path: Path):
    (tmp_path / "content").mkdir()
    exit_code = prompt.main(["UC-99.99.99", "--content-root", str(tmp_path / "content")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "lift-prompt:" in captured.err
    assert "UC-99.99.99" in captured.err
    assert captured.out == ""


def test_findings_section_splits_fixable_and_readonly(capsys, tmp_path: Path):
    content_root = _stage_minimal_sidecar(tmp_path)
    record = {
        "tier": "deep",
        "model": "claude-opus-5-5@reasoning=high",
        "content_sha256": "0" * 64,
        "findings": [
            {
                "field": "dataSources",
                "dimension": "correctness",
                "severity": "blocker",
                "explanation": "UPS-MIB has no battery-replace indicator.",
                "evidence_url": "https://mibs.observium.org/",
            },
            {"field": "premiumApps", "dimension": "overclaiming", "severity": "major", "explanation": "UBA not needed."},
        ],
        "firewalled_field_flags": [{"field": "spl", "issue": "timechart split twice", "severity": "blocker"}],
    }
    record_path = tmp_path / "record.json"
    record_path.write_text(json.dumps(record))
    exit_code = prompt.main(
        ["UC-15.1.1", "--content-root", str(content_root), "--findings", str(record_path)]
    )
    text = capsys.readouterr().out
    assert exit_code == 0
    assert "# REVIEW FINDINGS TO FIX (deep review by claude-opus-5-5@reasoning=high; recorded against an older" in text
    fixable = json.loads(re.search(r"## Fix in this diff.*?```json\n(.*?)\n```", text, re.DOTALL).group(1))
    readonly = json.loads(re.search(r"## Leave unchanged.*?```json\n(.*?)\n```", text, re.DOTALL).group(1))
    assert [f["field"] for f in fixable] == ["dataSources"]
    assert [f["field"] for f in readonly] == ["premiumApps", "spl"]


def test_findings_auto_without_record_fails(capsys, tmp_path: Path):
    content_root = _stage_minimal_sidecar(tmp_path)
    exit_code = prompt.main(["UC-15.1.1", "--content-root", str(content_root), "--findings", "auto"])
    assert exit_code in (0, 1)
    if exit_code == 1:
        assert "no review record" in capsys.readouterr().err


def test_handcraft_lists_v2_families(capsys, tmp_path: Path):
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(
        json.dumps(
            {
                "id": "15.1.1",
                "title": "T",
                "description": "Detects UC-15.1.1 on UPS feeds.",
                "value": "v",
                "dataSources": "d",
                "spl": "index=x",
                "detailedImplementation": "s",
            }
        )
    )
    prompt.main(["UC-15.1.1", "--content-root", str(tmp_path / "content"), "--handcraft"])
    text = capsys.readouterr().out
    assert "v2 template families: v2_description_selfref" in text
