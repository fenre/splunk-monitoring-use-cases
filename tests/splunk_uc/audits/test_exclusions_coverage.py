"""Unit tests for ``python -m splunk_uc audit-exclusions-coverage``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.audits import exclusions_coverage as ec  # noqa: E402


def _uc(
    uc_id: str = "1.1.1",
    *,
    exclusions: object | None = None,
    criticality: str = "medium",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": uc_id,
        "title": "Test UC",
        "criticality": criticality,
    }
    if exclusions is not None:
        payload["exclusions"] = exclusions
    return payload


def _write_sidecar(root: Path, category: int, uc_id: str, payload: dict[str, object]) -> Path:
    cat_dir = root / f"cat-{category:02d}-test"
    cat_dir.mkdir(parents=True, exist_ok=True)
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "payload, expected",
    [
        (_uc(exclusions=None), "missing"),
        ({"id": "1.1.1"}, "missing"),
        (_uc(exclusions=""), "too_short"),
        (_uc(exclusions="   "), "too_short"),
        (_uc(exclusions="x" * 9), "too_short"),
        (_uc(exclusions="x" * 10), "bare"),
        (_uc(exclusions="x" * 79), "bare"),
        (_uc(exclusions="x" * 80), "populated"),
        (_uc(exclusions="x" * 81), "populated"),
        (_uc(exclusions="x" * 400), "populated"),
        (_uc(exclusions="x" * 401), "verbose"),
    ],
)
def test_classify_exclusions_states(payload: dict[str, object], expected: str) -> None:
    assert ec.classify_exclusions(payload) == expected


def test_classify_exclusions_null_is_missing() -> None:
    assert ec.classify_exclusions(_uc(exclusions=None)) == "missing"


def test_classify_exclusions_respects_min_length_override() -> None:
    text = "a" * 50
    assert ec.classify_exclusions(_uc(exclusions=text), min_length=40) == "populated"
    assert ec.classify_exclusions(_uc(exclusions=text), min_length=60) == "bare"


def test_evaluate_coverage_fixture_counters(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, 1, "1.1.1", _uc("1.1.1", exclusions=None, criticality="high"))
    _write_sidecar(tmp_path, 1, "1.1.2", _uc("1.1.2", exclusions="", criticality="medium"))
    _write_sidecar(tmp_path, 2, "2.1.1", _uc("2.1.1", exclusions="x" * 20, criticality="low"))
    _write_sidecar(
        tmp_path,
        2,
        "2.1.2",
        _uc("2.1.2", exclusions="x" * 120, criticality="high"),
    )

    report = ec.evaluate_coverage(tmp_path)
    assert report.corpus_size == 4
    assert report.by_state["missing"] == 1
    assert report.by_state["too_short"] == 1
    assert report.by_state["bare"] == 1
    assert report.by_state["populated"] == 1
    assert report.by_category["1"]["missing"] == 1
    assert report.by_category["2"]["populated"] == 1
    assert [row.id for row in report.prioritized_queue] == ["UC-1.1.1", "UC-1.1.2"]


def test_evaluate_coverage_empty_corpus(tmp_path: Path) -> None:
    report = ec.evaluate_coverage(tmp_path)
    assert report.corpus_size == 0
    assert report.coverage_percent == 100.0
    assert report.prioritized_queue == []


def test_evaluate_coverage_criticality_filter(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, 1, "1.1.1", _uc("1.1.1", exclusions=None, criticality="high"))
    _write_sidecar(tmp_path, 1, "1.1.2", _uc("1.1.2", exclusions=None, criticality="low"))

    report = ec.evaluate_coverage(tmp_path, criticality_filter="high")
    assert len(report.prioritized_queue) == 1
    assert report.prioritized_queue[0].id == "UC-1.1.1"


def test_prioritized_queue_sort_order(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, 9, "9.2.1", _uc("9.2.1", exclusions=None, criticality="medium"))
    _write_sidecar(tmp_path, 1, "1.10.1", _uc("1.10.1", exclusions=None, criticality="high"))
    _write_sidecar(tmp_path, 1, "1.2.1", _uc("1.2.1", exclusions=None, criticality="high"))

    report = ec.evaluate_coverage(tmp_path)
    assert [row.id for row in report.prioritized_queue] == ["UC-1.2.1", "UC-1.10.1", "UC-9.2.1"]


def test_json_output_is_deterministic(tmp_path: Path) -> None:
    _write_sidecar(tmp_path, 1, "1.1.1", _uc("1.1.1", exclusions=None, criticality="high"))
    report = ec.evaluate_coverage(tmp_path)
    first = report.to_json_dict("2026-05-19T00:00:00Z")
    second = report.to_json_dict("2026-05-19T00:00:00Z")
    assert first == second
    assert list(first["by_state"].keys()) == list(ec.STATES)


def test_markdown_limit_caps_backlog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for idx in range(3):
        _write_sidecar(
            tmp_path,
            1,
            f"1.1.{idx + 1}",
            _uc(f"1.1.{idx + 1}", exclusions=None, criticality="high"),
        )
    report = ec.evaluate_coverage(tmp_path)
    md = ec.render_markdown(report, limit=2)
    assert "UC-1.1.1" in md
    assert "UC-1.1.2" in md
    assert "… and 1 more missing/too-short UCs." in md


def test_main_check_threshold_pass_and_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_sidecar(tmp_path, 1, "1.1.1", _uc("1.1.1", exclusions="x" * 100))
    _write_sidecar(tmp_path, 1, "1.1.2", _uc("1.1.2", exclusions=None))

    monkeypatch.setattr(ec, "CONTENT_ROOT", tmp_path)
    monkeypatch.setattr(ec, "REPO_ROOT", tmp_path)

    assert ec.main(["--check", "--threshold", "0", "--out", str(tmp_path / "out")]) == 0
    assert ec.main(["--check", "--threshold", "100", "--out", str(tmp_path / "out")]) == 1


def test_main_criticality_and_min_length_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_sidecar(tmp_path, 1, "1.1.1", _uc("1.1.1", exclusions="x" * 30, criticality="high"))
    monkeypatch.setattr(ec, "CONTENT_ROOT", tmp_path)
    monkeypatch.setattr(ec, "REPO_ROOT", tmp_path)

    out_dir = tmp_path / "reports"
    rc = ec.main(
        [
            "--min-length",
            "25",
            "--criticality",
            "high",
            "--out",
            str(out_dir),
        ]
    )
    assert rc == 0
    payload = json.loads((out_dir / "exclusions-coverage.json").read_text(encoding="utf-8"))
    assert payload["min_length"] == 25
    assert payload["by_state"]["populated"] == 1


def test_main_help_lists_flags() -> None:
    with pytest.raises(SystemExit) as exc:
        ec.main(["--help"])
    assert exc.value.code == 0
