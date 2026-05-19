"""Tests for ``splunk_uc.audits.cost_coverage``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import cost_coverage as cc

pytestmark = pytest.mark.usefixtures("tmp_path")


def _write_uc(root: Path, cat: str, uc_id: str, payload: dict) -> Path:
    cat_dir = root / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_evaluate_coverage_complete_partial_missing(tmp_path: Path) -> None:
    _write_uc(
        tmp_path,
        "cat-01-network",
        "1.1.1",
        {"id": "1.1.1", "title": "Complete UC", "cost": {"tier": "low"}},
    )
    _write_uc(
        tmp_path,
        "cat-01-network",
        "1.1.2",
        {"id": "1.1.2", "title": "Partial UC", "cost": {"search_load": "heavy"}},
    )
    _write_uc(
        tmp_path,
        "cat-02-security",
        "2.1.1",
        {"id": "2.1.1", "title": "Missing UC", "criticality": "high"},
    )

    report = cc.evaluate_coverage(tmp_path)

    assert report.total == 3
    assert report.complete == 1
    assert report.partial == 1
    assert report.missing == 1
    assert report.tier_coverage_pct == pytest.approx(100.0 / 3.0)


def test_coverage_report_json_is_deterministic_and_sorted(tmp_path: Path) -> None:
    _write_uc(
        tmp_path,
        "cat-10-security",
        "10.2.1",
        {"id": "10.2.1", "title": "B", "criticality": "medium"},
    )
    _write_uc(
        tmp_path,
        "cat-01-network",
        "1.1.1",
        {"id": "1.1.1", "title": "A", "cost": {"tier": "high"}},
    )

    report = cc.evaluate_coverage(tmp_path)
    first = cc._canonical_json(report.to_json_dict())
    second = cc._canonical_json(report.to_json_dict())

    assert first == second
    data = json.loads(first)
    assert list(data["by_category"].keys()) == sorted(
        data["by_category"].keys(), key=int
    )
    assert data["queue"][0]["uc_id"] == "10.2.1"


def test_main_check_threshold_zero_exits_zero(tmp_path: Path, capsys) -> None:
    _write_uc(
        tmp_path,
        "cat-01-network",
        "1.1.1",
        {"id": "1.1.1", "title": "No cost yet"},
    )

    rc = cc.main(
        [
            "--content-root",
            str(tmp_path),
            "--out",
            str(tmp_path / "report.json"),
            "--check",
            "--threshold",
            "0",
        ]
    )

    assert rc == 0
    assert "0/1 complete" in capsys.readouterr().out


def test_main_check_fails_below_threshold(tmp_path: Path) -> None:
    _write_uc(
        tmp_path,
        "cat-01-network",
        "1.1.1",
        {"id": "1.1.1", "title": "No cost yet"},
    )

    rc = cc.main(
        [
            "--content-root",
            str(tmp_path),
            "--out",
            str(tmp_path / "report.json"),
            "--check",
            "--threshold",
            "100",
        ]
    )

    assert rc == 1


def test_render_markdown_truncates_long_titles(tmp_path: Path) -> None:
    report = cc.evaluate_coverage(tmp_path)
    md = cc.render_markdown(report)
    assert "# Cost field coverage" in md
