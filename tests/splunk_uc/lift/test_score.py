"""Tests for the ``lift-score`` verb."""

from __future__ import annotations

import json
import re
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
    assert "UC: UC-15.1.1" in captured.out  # human-readable verb prints UC- prefix
    assert "current score" in captured.out.lower()
    assert "Failing fields:" in captured.out  # section header is present
    # `description` must appear as a field name in the failing-fields list,
    # not just incidentally in some other line.
    assert re.search(r"^\s*-\s+description:\s", captured.out, flags=re.MULTILINE), (
        f"expected '  - description: <msg>' line in:\n{captured.out}"
    )


def test_main_returns_1_with_stderr_for_unknown_uc(capsys, tmp_path: Path) -> None:
    (tmp_path / "content").mkdir()
    exit_code = score.main(["UC-99.99.99", "--content-root", str(tmp_path / "content")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "lift-score:" in captured.err
    assert "UC-99.99.99" in captured.err
    assert captured.out == ""  # nothing on stdout


def test_main_prints_clean_message_when_no_failing_fields(
    capsys, tmp_path: Path, monkeypatch
) -> None:
    """Pin the "All rubric fields satisfy the target tier." branch.

    Constructing a sidecar that genuinely passes silver/gold is
    fragile and ties this test to the evolving rubric; monkeypatching
    ``score_uc`` to return an empty failing-fields report makes the
    branch deterministic without coupling the test to rubric drift.
    """
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    (cat / "UC-15.1.1.json").write_text(json.dumps({"id": "15.1.1", "title": "x"}))

    class _FakeReport:
        uc_id = "15.1.1"
        current_score = 100
        failing_fields: dict[str, list[str]] = {}

        class target_tier:  # type: ignore[no-redef]
            value = "silver"

    monkeypatch.setattr(score, "score_uc", lambda *a, **kw: _FakeReport())
    exit_code = score.main(
        ["UC-15.1.1", "--content-root", str(tmp_path / "content")]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "All rubric fields satisfy the target tier." in captured.out


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
