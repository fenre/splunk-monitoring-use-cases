"""Tests for the ``lift-validate`` verb.

The verb is the §5 firewall: it must reject any diff that touches a
firewalled field, that fails to lift the score strictly, or whose
identity does not match the on-disk sidecar. On a clean diff it writes
the lifted content back to the sidecar and regenerates the markdown
companion (unless ``--dry-run`` or ``--skip-md-regen`` is set).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.lift import validate  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"
BRONZE = FIXTURE_DIR / "UC-15-bronze-baseline.json"
SILVER = FIXTURE_DIR / "UC-15-silver-target.json"


def _stage_uc(tmp_path: Path, fixture: Path = BRONZE) -> tuple[Path, Path]:
    """Copy the named fixture into a temp content tree."""
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    sidecar = cat / "UC-15.1.1.json"
    shutil.copy(fixture, sidecar)
    return tmp_path / "content", sidecar


def _write_diff(
    tmp_path: Path,
    uc_id: str,
    lifted: dict[str, object],
    *,
    target_tier: str = "silver",
    diff_uc_id: str | None = None,
) -> Path:
    diff_path = tmp_path / f"lift-{uc_id}.diff.json"
    payload = {
        "uc_id": diff_uc_id if diff_uc_id is not None else uc_id.removeprefix("UC-"),
        "target_tier": target_tier,
        "lifted_fields": lifted,
    }
    diff_path.write_text(json.dumps(payload))
    return diff_path


def _silver_lifted_fields() -> dict[str, object]:
    """Subset of the Silver fixture that, when applied to Bronze, lifts the score."""
    silver = json.loads(SILVER.read_text())
    return {
        "description": silver["description"],
        "value": silver["value"],
        "dataSources": silver["dataSources"],
        "detailedImplementation": silver["detailedImplementation"],
        "knownFalsePositives": silver["knownFalsePositives"],
        "references": silver["references"],
    }


def test_validate_accepts_proper_silver_lift(tmp_path: Path) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    after = json.loads(sidecar.read_text())
    silver = json.loads(SILVER.read_text())
    assert after["description"] == silver["description"]
    assert after["detailedImplementation"] == silver["detailedImplementation"]
    baseline = json.loads(BRONZE.read_text())
    assert after["spl"] == baseline["spl"]
    assert after["id"] == baseline["id"]


def test_validate_rejects_diff_that_touches_firewalled_field(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"spl": "search index=evil"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "firewall" in captured.err.lower()
    assert "spl" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_grandma_explanation(tmp_path: Path, capsys) -> None:
    """grandmaExplanation is firewalled — a dedicated generator owns it."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        {"grandmaExplanation": "We help keep computer rooms healthy."},
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "grandmaExplanation" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_field_outside_lift_surface(tmp_path: Path, capsys) -> None:
    """A field name that's not in LIFT_SURFACE_FIELDS is rejected."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"pancakes": "delicious"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "pancakes" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_when_post_score_not_strictly_greater(tmp_path: Path, capsys) -> None:
    """Applying an unchanged value must NOT raise the score."""
    content_root, sidecar = _stage_uc(tmp_path)
    baseline = json.loads(BRONZE.read_text())
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        {"description": baseline["description"]},
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "score" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == baseline


def test_validate_rejects_uc_id_mismatch(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        _silver_lifted_fields(),
        diff_uc_id="15.99.99",
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "uc_id" in captured.err.lower() or "id" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_target_tier_mismatch(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(
        tmp_path,
        "UC-15.1.1",
        _silver_lifted_fields(),
        target_tier="gold",
    )
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--target-tier",
            "silver",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "tier" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_rejects_malformed_diff(tmp_path: Path, capsys) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = tmp_path / "broken.diff.json"
    diff_path.write_text(json.dumps({"not_a_diff": True}))
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "diff" in captured.err.lower()
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_dry_run_does_not_write_sidecar(tmp_path: Path) -> None:
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--dry-run",
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_unknown_uc_returns_1(tmp_path: Path, capsys) -> None:
    (tmp_path / "content").mkdir()
    diff_path = _write_diff(tmp_path, "UC-99.99.99", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-99.99.99",
            "--diff",
            str(diff_path),
            "--content-root",
            str(tmp_path / "content"),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "lift-validate:" in captured.err
    assert "UC-99.99.99" in captured.err


def test_validate_emits_json_summary_on_success(tmp_path: Path, capsys) -> None:
    """The happy-path stdout payload is parseable JSON with before/after scores."""
    content_root, _sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
            "--json",
        ]
    )
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["uc_id"] == "UC-15.1.1"
    assert payload["score_before"] == 20
    assert payload["score_after"] > 20
    assert payload["wrote"].endswith("UC-15.1.1.json")


def test_validate_rejects_diff_with_value_of_wrong_type(tmp_path: Path, capsys) -> None:
    """references is array-typed; a string value must be rejected."""
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", {"references": "https://example.com"})
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "references" in captured.err
    assert json.loads(sidecar.read_text()) == json.loads(BRONZE.read_text())


def test_validate_writes_markdown_twin_when_md_regen_enabled(tmp_path: Path) -> None:
    """Without --skip-md-regen, lift-validate regenerates the .md twin.

    Exercises the ``generate-md-from-json --files`` subprocess so a
    regression in that path is caught here rather than at integration
    time. Subprocess overhead is ~50 ms; acceptable for one test.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    md_path = sidecar.with_suffix(".md")
    assert not md_path.exists()
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
        ]
    )
    assert exit_code == 0
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert "15.1.1" in md_content
    assert "APC Smart-UPS" in md_content


def test_validate_emits_canonical_utf8_when_writing(tmp_path: Path) -> None:
    """Written sidecar must use raw UTF-8, not ``\\u2014`` escape sequences.

    The catalog convention is raw UTF-8 (>97 % of UCs); a regression
    here would create a churn-storm of meaningless escape changes the
    next time anyone runs the lift loop.
    """
    content_root, sidecar = _stage_uc(tmp_path)
    diff_path = _write_diff(tmp_path, "UC-15.1.1", _silver_lifted_fields())
    exit_code = validate.main(
        [
            "UC-15.1.1",
            "--diff",
            str(diff_path),
            "--content-root",
            str(content_root),
            "--skip-md-regen",
        ]
    )
    assert exit_code == 0
    raw = sidecar.read_text(encoding="utf-8")
    assert "\u2014" in raw
    assert "\\u2014" not in raw
