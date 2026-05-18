"""Tests for the ``lift-score`` verb."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import score  # noqa: E402


def test_main_prints_human_readable_report_by_default(capsys, tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar_data = {
        "id": "15.1.1",
        "title": "Test UC",
        "description": "short",
        "value": "short",
        "dataSources": "tiny",
        "detailedImplementation": "stub",
        "spl": "search index=main",
    }
    (cat / "UC-15.1.1.json").write_text(json.dumps(sidecar_data))
    exit_code = score.main(["UC-15.1.1", "--content-root", str(tmp_path / "content")])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "UC-15.1.1" in captured.out
    assert "current score" in captured.out.lower()
    assert "description" in captured.out


def test_main_emits_json_with_flag(capsys, tmp_path: Path) -> None:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(
        json.dumps(
            {
                "id": "15.1.1",
                "title": "x",
                "description": "short",
                "value": "short",
                "dataSources": "tiny",
                "detailedImplementation": "stub",
                "spl": "search index=main",
            }
        )
    )
    exit_code = score.main(["UC-15.1.1", "--json", "--content-root", str(tmp_path / "content")])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["uc_id"] == "15.1.1"
    assert "current_score" in payload
    assert "failing_fields" in payload
