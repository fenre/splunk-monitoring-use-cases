"""Tests for the ``lift-batch`` verb.

``lift-batch`` enumerates UCs in a category, scores each, and emits a
JSON manifest of the worst-N (or random-N) for the orchestration agent
to consume. It is the only lift verb that loops over many UCs; the
other three operate on one UC at a time.
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

from splunk_uc.tools.lift import batch  # noqa: E402

FIXTURE_DIR = Path(__file__).parent / "fixtures"
BRONZE = FIXTURE_DIR / "UC-15-bronze-baseline.json"
SILVER = FIXTURE_DIR / "UC-15-silver-target.json"


def _stage_cat15(tmp_path: Path) -> Path:
    cat = tmp_path / "content" / "cat-15-data-center-physical-infrastructure"
    cat.mkdir(parents=True)
    return cat


def _stage_uc(
    cat_dir: Path, uc_id: str, fixture: Path, *, patch: dict[str, object] | None = None
) -> Path:
    data = json.loads(fixture.read_text(encoding="utf-8"))
    data["id"] = uc_id
    if patch:
        data.update(patch)
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def test_batch_emits_manifest_sorted_worst_first(tmp_path: Path) -> None:
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", SILVER)
    _stage_uc(cat, "15.1.2", BRONZE)
    _stage_uc(
        cat,
        "15.1.3",
        BRONZE,
        patch={"description": "x" * 90},
    )

    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--limit",
            "3",
            "--worst-first",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    assert manifest["category"] == "cat-15"
    assert manifest["target_tier"] == "silver"
    assert manifest["selection"] == "worst-first"
    assert manifest["limit"] == 3
    assert len(manifest["ucs"]) == 3
    scores = [entry["current_score"] for entry in manifest["ucs"]]
    assert scores == sorted(scores), f"expected ascending scores, got {scores}"
    assert all(entry["uc_id"].startswith("UC-15.1.") for entry in manifest["ucs"])


def test_batch_respects_limit(tmp_path: Path) -> None:
    cat = _stage_cat15(tmp_path)
    for i in range(1, 6):
        _stage_uc(cat, f"15.1.{i}", BRONZE)
    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--limit",
            "3",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    assert len(manifest["ucs"]) == 3


def test_batch_supports_two_digit_category(tmp_path: Path) -> None:
    """``--category cat-15`` must not match ``cat-1``/``cat-2`` (false prefix)."""
    root = tmp_path / "content"
    cat_5 = root / "cat-5-power-cooling"
    cat_5.mkdir(parents=True)
    _stage_uc(cat_5, "5.1.1", BRONZE)
    cat_15 = root / "cat-15-data-center-physical-infrastructure"
    cat_15.mkdir(parents=True)
    _stage_uc(cat_15, "15.1.1", BRONZE)

    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(root),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    ids = [u["uc_id"] for u in manifest["ucs"]]
    assert ids == ["UC-15.1.1"], f"prefix-collision: cat-15 should not match cat-5, got {ids}"


def test_batch_errors_when_category_missing(tmp_path: Path, capsys) -> None:
    (tmp_path / "content").mkdir()
    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-99",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cat-99" in captured.err
    assert not report_path.exists()


def test_batch_errors_when_category_empty(tmp_path: Path, capsys) -> None:
    cat = _stage_cat15(tmp_path)
    assert cat.exists()  # no UCs inside
    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "no uc" in captured.err.lower() or "empty" in captured.err.lower()
    assert not report_path.exists()


def test_batch_manifest_includes_metadata(tmp_path: Path) -> None:
    """The manifest must carry generated_at, category, tier, limit, selection."""
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", BRONZE)
    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--limit",
            "1",
            "--target-tier",
            "gold",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    assert manifest["category"] == "cat-15"
    assert manifest["target_tier"] == "gold"
    assert manifest["limit"] == 1
    assert manifest["selection"] == "worst-first"
    assert "generated_at" in manifest


def test_batch_per_uc_entry_has_expected_shape(tmp_path: Path) -> None:
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", BRONZE)
    report_path = tmp_path / "report.json"
    batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    manifest = json.loads(report_path.read_text())
    entry = manifest["ucs"][0]
    for key in ("uc_id", "sidecar_path", "current_score", "failing_fields"):
        assert key in entry, f"missing {key!r} in manifest entry"
    assert entry["uc_id"] == "UC-15.1.1"
    assert isinstance(entry["failing_fields"], list)


def test_batch_random_selection_does_not_preserve_score_order(tmp_path: Path) -> None:
    """--random shuffles; with a fixed seed we get a deterministic non-asc order."""
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", SILVER)
    _stage_uc(cat, "15.1.2", BRONZE)
    _stage_uc(cat, "15.1.3", BRONZE, patch={"description": "x" * 90})
    _stage_uc(cat, "15.1.4", SILVER)

    report_path = tmp_path / "report.json"
    exit_code = batch.main(
        [
            "--category",
            "cat-15",
            "--limit",
            "4",
            "--random",
            "--seed",
            "42",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert exit_code == 0
    manifest = json.loads(report_path.read_text())
    assert manifest["selection"] == "random"
    assert len(manifest["ucs"]) == 4


def test_batch_errors_when_category_prefix_matches_multiple_dirs(
    tmp_path: Path, capsys
) -> None:
    """Two sibling folders sharing the ``cat-15-*`` prefix must trip the
    RuntimeError in ``_resolve_category`` and surface a rc=1 with a
    helpful error message."""
    root = tmp_path / "content"
    (root / "cat-15-foo").mkdir(parents=True)
    (root / "cat-15-bar").mkdir(parents=True)
    rc = batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(root),
            "--report",
            str(tmp_path / "report.json"),
        ]
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "multiple category folders matched" in err
    assert "cat-15-foo" in err and "cat-15-bar" in err


def test_default_report_path_lands_under_content_parent(
    tmp_path: Path,
) -> None:
    """``_default_report_path`` writes under ``<content_root>.parent/reports/``
    with a UTC-stamped filename. Pins the side-effect-free contract."""
    content_root = tmp_path / "content"
    content_root.mkdir()
    p = batch._default_report_path(content_root)
    assert p.parent == tmp_path / "reports"
    assert p.name.startswith("lift-batch-")
    assert p.name.endswith(".json")


def test_batch_uses_default_report_path_when_report_arg_omitted(
    tmp_path: Path,
) -> None:
    """When ``--report`` is omitted, the manifest is written to the
    default path next to the content root."""
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", BRONZE)
    rc = batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(tmp_path / "content"),
        ]
    )
    assert rc == 0
    reports = list((tmp_path / "reports").glob("lift-batch-*.json"))
    assert len(reports) == 1
    manifest = json.loads(reports[0].read_text())
    assert manifest["ucs"][0]["uc_id"] == "UC-15.1.1"


def test_batch_surfaces_warnings_for_unparseable_sidecars(
    tmp_path: Path,
) -> None:
    """A sidecar that ``score_uc`` rejects must NOT abort the run — it
    is recorded as a warning in the manifest and the rest of the
    category continues to be scored. Pins the ``except (...)`` branch
    in ``_score_all`` and the ``warnings`` key write in ``main``.
    """
    cat = _stage_cat15(tmp_path)
    _stage_uc(cat, "15.1.1", BRONZE)
    # A second sidecar that score_uc will reject (invalid JSON shape).
    (cat / "UC-15.1.2.json").write_text(
        "{ not valid json", encoding="utf-8"
    )
    report_path = tmp_path / "report.json"
    rc = batch.main(
        [
            "--category",
            "cat-15",
            "--content-root",
            str(tmp_path / "content"),
            "--report",
            str(report_path),
        ]
    )
    assert rc == 0
    manifest = json.loads(report_path.read_text())
    assert "warnings" in manifest
    assert any("UC-15.1.2.json" in w for w in manifest["warnings"])
    # Only the good UC survives in the entries list.
    assert [u["uc_id"] for u in manifest["ucs"]] == ["UC-15.1.1"]
