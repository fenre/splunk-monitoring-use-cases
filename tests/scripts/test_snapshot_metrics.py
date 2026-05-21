"""Unit tests for ``scripts/snapshot_metrics.py``.

Repo-overhaul plan §P8 step 2 (2026-05-09): release-time snapshots
of ``dist/metrics.json`` under ``data/metrics-history/<VERSION>.json``
are the only mechanism preserving release-over-release trend signals
once the live build is recomputed. A regression in the snapshot
script (silently overwriting wrong files, drifting index, schema
violation) would mean a release ships *and the trend record never
updates* — which we'd discover months later when somebody asked
"how did MITRE coverage change between 9.1 and 9.5?".

The tests exercise:

* Pure helpers (`_read_version`, `_validate_metrics_shape`,
  `_semver_key`, `_refresh_index`) on synthetic fixtures.
* End-to-end `--write` and `--check` round trips on a tmp working
  tree so the assertions don't depend on the live repo state.
* Drift detection: missing snapshot, malformed JSON, version
  mismatch, index out of sync, schema mismatch with live build.
* Idempotency: writing twice in a row produces the same on-disk
  index (only `capturedAt` may change in the snapshot itself).
* Live smoke: the committed ``data/metrics-history/`` and
  ``schemas/v2/metrics-history-index.schema.json`` parse and
  validate the index, so any bit-rot in the committed snapshot
  fails CI immediately.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "snapshot_metrics.py"
LIVE_INDEX = REPO_ROOT / "data" / "metrics-history" / "index.json"
LIVE_INDEX_SCHEMA = REPO_ROOT / "schemas" / "v2" / "metrics-history-index.schema.json"
LIVE_HISTORY_DIR = REPO_ROOT / "data" / "metrics-history"


def _load_module() -> ModuleType:
    """Import the snapshot script as a module without polluting sys.path."""
    spec = importlib.util.spec_from_file_location("snapshot_metrics", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["snapshot_metrics"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def snap() -> ModuleType:
    return _load_module()


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------


def _well_formed_metrics(catalogue_version: str = "9.2.0", uc_count: int = 7677) -> dict[str, Any]:
    """A metrics.json payload satisfying ``_validate_metrics_shape``."""
    return {
        "$schema": "/schemas/v2/metrics.schema.json",
        "schema_version": "1.0.0",
        "catalogueVersion": catalogue_version,
        "generatedAt": "2026-05-07T00:00:00Z",
        "build": {"reproducible": True, "platform": "ci", "python": "3.14.4"},
        "counts": {
            "categories": 23,
            "subcategories": 239,
            "useCases": uc_count,
            "regulations": 69,
            "equipment": 105,
        },
        "quality": {"gold": 100, "silver": 200, "bronze": 300, "none": 0},
        "coverage": {},
        "distributions": {},
        "ucsByCategory": {},
        "leaderboards": {},
        "depth": {},
    }


def _scaffold(tmp_path: Path, *, version: str = "9.2.0", live_metrics: bool = True) -> dict[str, Path]:
    """Build a tmp working tree with VERSION + dist/metrics.json + history dir."""
    version_file = tmp_path / "VERSION"
    version_file.write_text(version + "\n", encoding="utf-8")
    history_dir = tmp_path / "data" / "metrics-history"
    history_dir.mkdir(parents=True)
    index_path = history_dir / "index.json"
    metrics_path = tmp_path / "dist" / "metrics.json"
    if live_metrics:
        metrics_path.parent.mkdir(parents=True)
        metrics_path.write_text(
            json.dumps(_well_formed_metrics(version), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "version_file": version_file,
        "history_dir": history_dir,
        "index_path": index_path,
        "metrics_path": metrics_path,
    }


# ---------------------------------------------------------------------------
# 1. Pure helpers
# ---------------------------------------------------------------------------


def test_read_version_strips_whitespace(snap: ModuleType, tmp_path: Path) -> None:
    """Whitespace and trailing newlines must be stripped — VERSION is single-line."""
    p = tmp_path / "VERSION"
    p.write_text("  9.2.0  \n\n", encoding="utf-8")
    assert snap._read_version(p) == "9.2.0"


def test_read_version_missing_file_exits_2(snap: ModuleType, tmp_path: Path) -> None:
    """A missing VERSION file must hit exit code 2, not silently default."""
    with pytest.raises(SystemExit) as exc_info:
        snap._read_version(tmp_path / "NO_VERSION")
    assert exc_info.value.code == 2


def test_read_version_empty_file_exits_2(snap: ModuleType, tmp_path: Path) -> None:
    """An empty VERSION file must also hit exit code 2."""
    p = tmp_path / "VERSION"
    p.write_text("   \n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        snap._read_version(p)
    assert exc_info.value.code == 2


def test_validate_metrics_shape_happy_path(snap: ModuleType, tmp_path: Path) -> None:
    """Well-formed payload reports zero defects."""
    issues = snap._validate_metrics_shape(_well_formed_metrics(), source=tmp_path / "x.json")
    assert issues == []


def test_validate_metrics_shape_missing_schema_version(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Empty schema_version is reported."""
    payload = _well_formed_metrics()
    del payload["schema_version"]
    issues = snap._validate_metrics_shape(payload, source=tmp_path / "x.json")
    assert any("schema_version" in i for i in issues)


def test_validate_metrics_shape_non_string_catalogue_version(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Non-string catalogueVersion is reported."""
    payload = _well_formed_metrics()
    payload["catalogueVersion"] = 9
    issues = snap._validate_metrics_shape(payload, source=tmp_path / "x.json")
    assert any("catalogueVersion" in i for i in issues)


def test_validate_metrics_shape_missing_use_case_count(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Missing counts.useCases is reported as a defect."""
    payload = _well_formed_metrics()
    del payload["counts"]["useCases"]
    issues = snap._validate_metrics_shape(payload, source=tmp_path / "x.json")
    assert any("useCases" in i for i in issues)


def test_validate_metrics_shape_wrong_schema_ref(
    snap: ModuleType, tmp_path: Path
) -> None:
    """$schema must point at metrics.schema.json or be flagged."""
    payload = _well_formed_metrics()
    payload["$schema"] = "/schemas/v2/something-else.schema.json"
    issues = snap._validate_metrics_shape(payload, source=tmp_path / "x.json")
    assert any("$schema" in i for i in issues)


def test_semver_key_orders_correctly(snap: ModuleType) -> None:
    """Sort key for semver returns ascending tuples; later releases sort higher."""
    assert snap._semver_key("9.2.0") > snap._semver_key("9.1.99")
    assert snap._semver_key("10.0.0") > snap._semver_key("9.99.99")
    assert snap._semver_key("1.0") == (1, 0, 0)


def test_semver_key_handles_garbage(snap: ModuleType) -> None:
    """Unparseable strings collapse to a sentinel rather than crashing."""
    assert snap._semver_key("garbage") == (0,)
    assert snap._semver_key("") == (0,)


def test_semver_key_strips_prerelease_suffix(snap: ModuleType) -> None:
    """Pre-release suffixes are dropped; only the X.Y.Z prefix is sorted."""
    assert snap._semver_key("9.2.0-rc1") == (9, 2, 0)
    assert snap._semver_key("9.2.0+build123") == (9, 2, 0)


# ---------------------------------------------------------------------------
# 2. Index refresh
# ---------------------------------------------------------------------------


def test_refresh_index_empty_dir_returns_skeleton(
    snap: ModuleType, tmp_path: Path
) -> None:
    """An empty history dir produces an index with empty snapshot list."""
    history = tmp_path / "history"
    history.mkdir()
    idx = snap._refresh_index(history, history / "index.json")
    assert idx["schema_version"] == snap.INDEX_SCHEMA_VERSION
    assert idx["snapshots"] == []


def test_refresh_index_sorts_descending_by_semver(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Newest releases first — humans scanning the file want the most recent on top."""
    history = tmp_path / "history"
    history.mkdir()
    for v in ["9.0.0", "10.1.0", "9.2.0", "8.5.0"]:
        (history / f"{v}.json").write_text(
            json.dumps(_well_formed_metrics(v)), encoding="utf-8"
        )
    idx = snap._refresh_index(history, history / "index.json")
    versions = [s["version"] for s in idx["snapshots"]]
    assert versions == ["10.1.0", "9.2.0", "9.0.0", "8.5.0"]


def test_refresh_index_skips_unparseable_files(
    snap: ModuleType, tmp_path: Path
) -> None:
    """A garbled JSON file in the history dir is silently skipped."""
    history = tmp_path / "history"
    history.mkdir()
    (history / "9.2.0.json").write_text(
        json.dumps(_well_formed_metrics()), encoding="utf-8"
    )
    (history / "broken.json").write_text("{not json", encoding="utf-8")
    idx = snap._refresh_index(history, history / "index.json")
    assert [s["version"] for s in idx["snapshots"]] == ["9.2.0"]


def test_refresh_index_excludes_index_itself(snap: ModuleType, tmp_path: Path) -> None:
    """The index file must not list itself when re-derived."""
    history = tmp_path / "history"
    history.mkdir()
    (history / "9.2.0.json").write_text(
        json.dumps(_well_formed_metrics()), encoding="utf-8"
    )
    (history / "index.json").write_text(
        json.dumps({"schema_version": "1.0.0", "snapshots": []}),
        encoding="utf-8",
    )
    idx = snap._refresh_index(history, history / "index.json")
    versions = [s["version"] for s in idx["snapshots"]]
    assert "index" not in versions
    assert versions == ["9.2.0"]


# ---------------------------------------------------------------------------
# 3. write_snapshot
# ---------------------------------------------------------------------------


def test_write_snapshot_creates_files(snap: ModuleType, tmp_path: Path) -> None:
    """A first-time write creates the snapshot, the index, and parent dirs."""
    s = _scaffold(tmp_path)
    dest = snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert dest == s["history_dir"] / "9.2.0.json"
    assert dest.exists()
    assert s["index_path"].exists()
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["catalogueVersion"] == "9.2.0"


def test_write_snapshot_is_verbatim_copy(snap: ModuleType, tmp_path: Path) -> None:
    """Snapshot must be a verbatim copy of dist/metrics.json — no synthetic fields.

    This is what lets the committed snapshot validate against the
    same ``schemas/v2/metrics.schema.json`` (which has
    ``additionalProperties: false``) as the live build artefact.
    """
    s = _scaffold(tmp_path)
    dest = snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    live = json.loads(s["metrics_path"].read_text(encoding="utf-8"))
    snapshot = json.loads(dest.read_text(encoding="utf-8"))
    assert set(snapshot.keys()) == set(live.keys())


def test_write_snapshot_byte_identical_on_repeat(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Writing twice with the same metrics produces byte-identical files.

    Since the snapshot is a verbatim copy of dist/metrics.json (no
    timestamp injected at write-time), idempotency is unconditional —
    not just the index, but the snapshot file itself.
    """
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    first_index = s["index_path"].read_bytes()
    first_snapshot = (s["history_dir"] / "9.2.0.json").read_bytes()
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    second_index = s["index_path"].read_bytes()
    second_snapshot = (s["history_dir"] / "9.2.0.json").read_bytes()
    assert first_index == second_index
    assert first_snapshot == second_snapshot


def test_write_snapshot_rejects_malformed_metrics(
    snap: ModuleType, tmp_path: Path
) -> None:
    """A live build emitting a malformed metrics.json must fail fast (exit 1)."""
    s = _scaffold(tmp_path, live_metrics=False)
    s["metrics_path"].parent.mkdir(parents=True)
    s["metrics_path"].write_text(json.dumps({"oops": True}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        snap.write_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
    assert exc_info.value.code == 1


def test_write_snapshot_missing_metrics_raises(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Missing dist/metrics.json must surface as FileNotFoundError to the CLI."""
    s = _scaffold(tmp_path, live_metrics=False)
    with pytest.raises(FileNotFoundError):
        snap.write_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )


def test_write_snapshot_records_new_release(snap: ModuleType, tmp_path: Path) -> None:
    """Writing for a fresh version adds a new entry to the index in correct order."""
    s = _scaffold(tmp_path, version="9.2.0")
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    s["version_file"].write_text("9.3.0\n", encoding="utf-8")
    s["metrics_path"].write_text(
        json.dumps(_well_formed_metrics("9.3.0", 8000), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    idx = json.loads(s["index_path"].read_text(encoding="utf-8"))
    versions = [entry["version"] for entry in idx["snapshots"]]
    assert versions == ["9.3.0", "9.2.0"], "newest release must appear first"


# ---------------------------------------------------------------------------
# 4. check_snapshot
# ---------------------------------------------------------------------------


def test_check_snapshot_happy_path(snap: ModuleType, tmp_path: Path) -> None:
    """A freshly-written snapshot must pass --check."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert failures == []


def test_check_snapshot_missing_for_current_version(
    snap: ModuleType, tmp_path: Path
) -> None:
    """If VERSION is bumped without snapshotting, --check must fail loudly."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    s["version_file"].write_text("9.3.0\n", encoding="utf-8")
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert any("missing snapshot" in f for f in failures)


def test_check_snapshot_catalogue_version_mismatch(
    snap: ModuleType, tmp_path: Path
) -> None:
    """A snapshot whose catalogueVersion disagrees with VERSION must fail."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    snapshot_path = s["history_dir"] / "9.2.0.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["catalogueVersion"] = "8.0.0"
    snapshot_path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert any("catalogueVersion" in f for f in failures)


def test_check_snapshot_index_drift(snap: ModuleType, tmp_path: Path) -> None:
    """A hand-edited index that no longer matches the directory must fail."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    idx = json.loads(s["index_path"].read_text(encoding="utf-8"))
    idx["snapshots"].append(
        {
            "file": "8.0.0.json",
            "version": "8.0.0",
            "schemaVersion": "1.0.0",
            "generatedAt": "2026-01-01T00:00:00Z",
            "useCases": 7000,
        }
    )
    s["index_path"].write_text(
        json.dumps(idx, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert any("out of sync" in f for f in failures)


def test_check_snapshot_schema_version_mismatch_with_live_build(
    snap: ModuleType, tmp_path: Path
) -> None:
    """When live build emits a newer schema_version than the committed snapshot, fail."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    live = json.loads(s["metrics_path"].read_text(encoding="utf-8"))
    live["schema_version"] = "2.0.0"
    s["metrics_path"].write_text(
        json.dumps(live, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert any("schema_version" in f for f in failures)


def test_check_snapshot_skips_schema_check_when_live_missing(
    snap: ModuleType, tmp_path: Path
) -> None:
    """Without a live dist/metrics.json (clean checkout) the schema gate is skipped."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    s["metrics_path"].unlink()
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert failures == []


def test_check_snapshot_malformed_committed_snapshot(
    snap: ModuleType, tmp_path: Path
) -> None:
    """A committed snapshot whose payload is not an object must be flagged."""
    s = _scaffold(tmp_path)
    snap.write_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    snapshot_path = s["history_dir"] / "9.2.0.json"
    snapshot_path.write_text("[1,2,3]", encoding="utf-8")
    s["index_path"].write_text(
        json.dumps(
            snap._refresh_index(s["history_dir"], s["index_path"]),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    failures = snap.check_snapshot(
        metrics_path=s["metrics_path"],
        history_dir=s["history_dir"],
        index_path=s["index_path"],
        version_file=s["version_file"],
    )
    assert any("not an object" in f for f in failures)


# ---------------------------------------------------------------------------
# 5. CLI main()
# ---------------------------------------------------------------------------


def test_main_write_then_check_round_trip(
    snap: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Round-trip: write succeeds (rc=0) and the next check succeeds (rc=0)."""
    s = _scaffold(tmp_path)
    rc_write = snap.main(
        [
            "--write",
            "--metrics", str(s["metrics_path"]),
            "--history-dir", str(s["history_dir"]),
            "--index", str(s["index_path"]),
            "--version-file", str(s["version_file"]),
        ]
    )
    assert rc_write == 0
    rc_check = snap.main(
        [
            "--check",
            "--metrics", str(s["metrics_path"]),
            "--history-dir", str(s["history_dir"]),
            "--index", str(s["index_path"]),
            "--version-file", str(s["version_file"]),
        ]
    )
    assert rc_check == 0
    captured = capsys.readouterr()
    assert "OK" in captured.out


def test_main_check_returns_1_on_drift(
    snap: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--check exits 1 (not raise) when a snapshot is missing for current VERSION."""
    s = _scaffold(tmp_path, live_metrics=False)
    rc = snap.main(
        [
            "--check",
            "--metrics", str(s["metrics_path"]),
            "--history-dir", str(s["history_dir"]),
            "--index", str(s["index_path"]),
            "--version-file", str(s["version_file"]),
        ]
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "drift detected" in captured.err


def test_main_write_returns_2_when_metrics_missing(
    snap: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--write exits 2 when dist/metrics.json is absent (operator hasn't built)."""
    s = _scaffold(tmp_path, live_metrics=False)
    rc = snap.main(
        [
            "--write",
            "--metrics", str(s["metrics_path"]),
            "--history-dir", str(s["history_dir"]),
            "--index", str(s["index_path"]),
            "--version-file", str(s["version_file"]),
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_requires_one_of_write_or_check(snap: ModuleType) -> None:
    """argparse must reject calls that pass neither (or both) of --write/--check."""
    with pytest.raises(SystemExit):
        snap.main([])


# ---------------------------------------------------------------------------
# 6. Live smoke — committed history must always validate
# ---------------------------------------------------------------------------


def test_live_index_exists_and_parses(snap: ModuleType) -> None:
    """The committed index.json must always parse; otherwise CI is blind."""
    if not LIVE_INDEX.exists():
        pytest.skip("data/metrics-history/index.json not committed yet")
    data = json.loads(LIVE_INDEX.read_text(encoding="utf-8"))
    assert isinstance(data.get("snapshots"), list)
    assert data["schema_version"] == snap.INDEX_SCHEMA_VERSION


def test_live_index_schema_loads(snap: ModuleType) -> None:
    """The accompanying JSON Schema for the index must parse and reference $defs cleanly."""
    if not LIVE_INDEX_SCHEMA.exists():
        pytest.skip("schemas/v2/metrics-history-index.schema.json not committed yet")
    schema = json.loads(LIVE_INDEX_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "snapshots" in schema["properties"]


def test_live_history_dir_files_match_index(snap: ModuleType) -> None:
    """Every *.json under data/metrics-history/ (other than index.json) must appear in index."""
    if not LIVE_INDEX.exists() or not LIVE_HISTORY_DIR.exists():
        pytest.skip("metrics history not committed yet")
    derived = snap._refresh_index(LIVE_HISTORY_DIR, LIVE_INDEX)
    on_disk_text = LIVE_INDEX.read_text(encoding="utf-8")
    derived_text = (
        json.dumps(derived, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )
    assert on_disk_text == derived_text, (
        "data/metrics-history/index.json is out of sync with snapshot files; "
        "run `make snapshot-metrics` to refresh"
    )


def test_live_snapshots_are_well_formed(snap: ModuleType) -> None:
    """Every committed snapshot file must satisfy _validate_metrics_shape."""
    if not LIVE_HISTORY_DIR.exists():
        pytest.skip("metrics history not committed yet")
    files = sorted(p for p in LIVE_HISTORY_DIR.glob("*.json") if p.name != "index.json")
    if not files:
        pytest.skip("no snapshots committed yet")
    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        issues = snap._validate_metrics_shape(payload, source=f)
        assert issues == [], f"{f}: {issues}"


def test_live_snapshots_validate_against_metrics_schema(snap: ModuleType) -> None:
    """Every committed snapshot must validate against schemas/v2/metrics.schema.json.

    Because the snapshot is a verbatim copy of ``dist/metrics.json``
    (no synthetic fields injected), and ``metrics.schema.json`` has
    ``additionalProperties: false``, this gate catches the moment a
    snapshot file drifts from the canonical wire format — most
    likely scenario: a maintainer hand-edits a snapshot to backfill
    a metric without bumping ``schema_version``.
    """
    metrics_schema_path = REPO_ROOT / "schemas" / "v2" / "metrics.schema.json"
    if not LIVE_HISTORY_DIR.exists() or not metrics_schema_path.exists():
        pytest.skip("metrics history or schema not committed yet")
    files = sorted(p for p in LIVE_HISTORY_DIR.glob("*.json") if p.name != "index.json")
    if not files:
        pytest.skip("no snapshots committed yet")

    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(metrics_schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for f in files:
        payload = json.loads(f.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path))
        assert errors == [], (
            f"{f}: snapshot does not validate against metrics.schema.json: "
            + "; ".join(f"{list(e.absolute_path)}: {e.message}" for e in errors[:5])
        )


# ---------------------------------------------------------------------------
# 9. Loader / index error paths (lines 121-126 + 165-180)
# ---------------------------------------------------------------------------


class TestLoadMetricsErrorPaths:
    """Cover the three failure modes of ``_load_metrics``: missing file
    (FileNotFoundError, the only path the caller catches), malformed
    JSON (SystemExit 2), and non-dict top-level (SystemExit 2).
    """

    def test_missing_file_raises_filenotfounderror(
        self, snap: ModuleType, tmp_path: Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            snap._load_metrics(tmp_path / "absent.json")

    def test_malformed_json_exits_2_with_fatal_message(
        self,
        snap: ModuleType,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closes lines 121-123: ``json.JSONDecodeError`` triggers a
        ``FATAL: malformed JSON`` message on stderr and ``exit(2)``.
        """
        p = tmp_path / "metrics.json"
        p.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            snap._load_metrics(p)
        assert exc_info.value.code == 2
        assert "FATAL: malformed JSON" in capsys.readouterr().err

    def test_non_dict_top_level_exits_2(
        self,
        snap: ModuleType,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closes lines 124-126: a JSON array (top-level list) is
        rejected with ``FATAL: ... top-level is not an object``.
        """
        p = tmp_path / "metrics.json"
        p.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            snap._load_metrics(p)
        assert exc_info.value.code == 2
        assert "top-level is not an object" in capsys.readouterr().err


class TestLoadIndexErrorPaths:
    """Cover the three branches of ``_load_index``: missing file
    (returns fresh skeleton — happy path), malformed JSON (SystemExit
    2), and shape-rejection (SystemExit 2).
    """

    def test_missing_file_returns_fresh_skeleton(
        self, snap: ModuleType, tmp_path: Path
    ) -> None:
        out = snap._load_index(tmp_path / "absent.json")
        assert out["schema_version"] == snap.INDEX_SCHEMA_VERSION
        assert out["snapshots"] == []
        assert out["$schema"].endswith("metrics-history-index.schema.json")

    def test_malformed_json_exits_2(
        self,
        snap: ModuleType,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closes lines 174-176: ``json.JSONDecodeError`` on the
        index file is fatal — we never want to silently overwrite a
        corrupted index with derived contents."""
        p = tmp_path / "index.json"
        p.write_text("not even json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            snap._load_index(p)
        assert exc_info.value.code == 2
        assert "FATAL: malformed index file" in capsys.readouterr().err

    def test_top_level_array_exits_2(
        self,
        snap: ModuleType,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Closes line 177-180 branch where the top level is not a
        dict (e.g. an accidental JSON array)."""
        p = tmp_path / "index.json"
        p.write_text(json.dumps([{"version": "9.2.0"}]), encoding="utf-8")
        with pytest.raises(SystemExit) as exc_info:
            snap._load_index(p)
        assert exc_info.value.code == 2
        assert "unexpected shape" in capsys.readouterr().err

    def test_dict_without_snapshots_key_exits_2(
        self,
        snap: ModuleType,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A dict whose ``snapshots`` field is not a list is also
        rejected — covers the second clause of the same ``if``."""
        p = tmp_path / "index.json"
        p.write_text(
            json.dumps({"snapshots": "not a list"}), encoding="utf-8"
        )
        with pytest.raises(SystemExit) as exc_info:
            snap._load_index(p)
        assert exc_info.value.code == 2
        assert "unexpected shape" in capsys.readouterr().err

    def test_valid_index_file_returns_parsed_data(
        self, snap: ModuleType, tmp_path: Path
    ) -> None:
        """Closes line 180 (the happy-path ``return data``): when
        the index file exists, parses as JSON, has dict top-level
        and a list ``snapshots`` field, the contents are returned
        unchanged.

        Note: ``_load_index`` is module-internal and currently not
        called by any other helper in ``snapshot_metrics.py`` (the
        write path uses ``_refresh_index`` directly and the check
        path goes through ``_check_index`` → ``_refresh_index``).
        This branch is therefore reachable only by direct call
        from a downstream consumer or from tests.
        """
        p = tmp_path / "index.json"
        payload = {
            "$schema": "/schemas/v2/metrics-history-index.schema.json",
            "schema_version": snap.INDEX_SCHEMA_VERSION,
            "snapshots": [
                {"version": "9.2.0", "path": "9.2.0.json"},
            ],
        }
        p.write_text(json.dumps(payload), encoding="utf-8")
        out = snap._load_index(p)
        assert out == payload
        assert isinstance(out["snapshots"], list)


# ---------------------------------------------------------------------------
# 10. Drift-detection branches in _check_snapshot (lines 332-334, 353-354, 371)
# ---------------------------------------------------------------------------


class TestCheckSnapshotDriftBranches:
    """Lines 332-334, 353-354, 356-365, 371 are reached only from
    inside ``_check_snapshot`` and only by very specific drift
    conditions. The end-to-end ``--check`` path exercises one happy
    branch but not these defensive ones.
    """

    def test_malformed_snapshot_json_recorded_as_failure(
        self, snap: ModuleType, tmp_path: Path
    ) -> None:
        """Closes lines 332-334: snapshot file is present but its
        JSON is malformed — ``--check`` records the defect and
        bails out of the rest of the snapshot inspection.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_path.write_text("{broken json", encoding="utf-8")
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        assert any("malformed JSON" in f for f in failures)

    def test_non_dict_snapshot_top_level_recorded_as_failure(
        self,
        snap: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Closes lines 336-338: a snapshot whose top-level is a list
        instead of a dict is recorded as ``top-level is not an
        object`` and short-circuits the rest of the inspection.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_path.write_text(json.dumps(["x", "y"]), encoding="utf-8")
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        assert any("top-level is not an object" in f for f in failures)

    def test_live_metrics_malformed_short_circuits_schema_compare(
        self,
        snap: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Closes lines 353-354: when the live ``dist/metrics.json``
        is malformed, ``_load_metrics`` raises ``SystemExit`` (which
        is caught) and we ``return failures`` *without* attempting
        the schema-version comparison. The snapshot itself is fine;
        the live build is broken; we still surface that as the
        only failure.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_path.write_text(
            json.dumps(_well_formed_metrics("9.2.0"), indent=2) + "\n",
            encoding="utf-8",
        )
        snap._refresh_index(s["history_dir"], s["index_path"])
        derived = snap._refresh_index(s["history_dir"], s["index_path"])
        s["index_path"].write_text(
            json.dumps(
                derived, ensure_ascii=False, sort_keys=True, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        s["metrics_path"].parent.mkdir(parents=True, exist_ok=True)
        s["metrics_path"].write_text("{broken", encoding="utf-8")
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        # Schema comparison was skipped (no message mentions
        # "schema_version is ..."); the only path that could have
        # surfaced one is gated by the ``try/except SystemExit``.
        assert all("snapshot schema_version is" not in f for f in failures)

    def test_live_metrics_different_catalogue_version_skips_schema_compare(
        self,
        snap: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Closes branch 356->365: when the live build's
        ``catalogueVersion`` does NOT match VERSION, the
        schema-version comparison is INTENTIONALLY SKIPPED. This
        protects the gate during transition periods: VERSION bumps
        to 9.3.0 in the same PR that bumps schema_version, but
        ``dist/metrics.json`` may still carry the previous
        ``catalogueVersion`` until ``make build`` runs locally.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_payload = _well_formed_metrics("9.2.0")
        snapshot_payload["schema_version"] = "1.0.0"
        snapshot_path.write_text(
            json.dumps(snapshot_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        derived = snap._refresh_index(s["history_dir"], s["index_path"])
        s["index_path"].write_text(
            json.dumps(
                derived, ensure_ascii=False, sort_keys=True, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        s["metrics_path"].parent.mkdir(parents=True, exist_ok=True)
        # Live build is from an OLDER catalogueVersion AND a
        # different schema_version — but since the cat-ver does
        # not match VERSION, no schema_version failure is emitted.
        live_payload = _well_formed_metrics("9.1.0")
        live_payload["schema_version"] = "0.9.0"
        s["metrics_path"].write_text(
            json.dumps(live_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        # Schema-version mismatch is NOT raised because cat-vers
        # diverge; the rest of the snapshot inspection still passes.
        assert all(
            "snapshot schema_version is" not in f for f in failures
        )

    def test_live_metrics_schema_version_match_records_no_failure(
        self,
        snap: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Closes branch 356->365: when the live build's
        ``catalogueVersion`` equals VERSION AND the live
        ``schema_version`` MATCHES the snapshot's, NO failure is
        emitted by this comparison block. The test confirms the
        check is a true equality test, not a one-sided guard.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_payload = _well_formed_metrics("9.2.0")
        snapshot_payload["schema_version"] = "1.0.0"
        snapshot_path.write_text(
            json.dumps(snapshot_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        derived = snap._refresh_index(s["history_dir"], s["index_path"])
        s["index_path"].write_text(
            json.dumps(
                derived, ensure_ascii=False, sort_keys=True, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        s["metrics_path"].parent.mkdir(parents=True, exist_ok=True)
        live_payload = _well_formed_metrics("9.2.0")
        live_payload["schema_version"] = "1.0.0"  # matches snapshot
        s["metrics_path"].write_text(
            json.dumps(live_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        # No failures from the schema-version comparison branch.
        assert all(
            "snapshot schema_version is" not in f for f in failures
        )

    def test_live_metrics_schema_version_mismatch_recorded(
        self,
        snap: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Closes line 356-365 branch where the live build emits a
        DIFFERENT ``schema_version`` than the committed snapshot.
        This is the canonical drift scenario after a schema bump
        without a fresh snapshot.
        """
        s = _scaffold(tmp_path, live_metrics=False)
        snapshot_path = s["history_dir"] / "9.2.0.json"
        snapshot_payload = _well_formed_metrics("9.2.0")
        snapshot_payload["schema_version"] = "1.0.0"
        snapshot_path.write_text(
            json.dumps(snapshot_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        derived = snap._refresh_index(s["history_dir"], s["index_path"])
        s["index_path"].write_text(
            json.dumps(
                derived, ensure_ascii=False, sort_keys=True, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        s["metrics_path"].parent.mkdir(parents=True, exist_ok=True)
        live_payload = _well_formed_metrics("9.2.0")
        live_payload["schema_version"] = "1.1.0"
        s["metrics_path"].write_text(
            json.dumps(live_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        failures = snap.check_snapshot(
            metrics_path=s["metrics_path"],
            history_dir=s["history_dir"],
            index_path=s["index_path"],
            version_file=s["version_file"],
        )
        assert any(
            "snapshot schema_version is '1.0.0'" in f
            and "live build emits '1.1.0'" in f
            for f in failures
        )


class TestCheckIndexMissingPath:
    """Closes line 371: ``_check_index`` returns a single
    ``missing index at <path>`` failure when ``index.json`` is
    absent.
    """

    def test_missing_index_returns_failure(
        self, snap: ModuleType, tmp_path: Path
    ) -> None:
        history = tmp_path / "history"
        history.mkdir()
        index_path = history / "index.json"
        assert not index_path.exists()
        failures = snap._check_index(history, index_path)
        assert len(failures) == 1
        assert "missing index" in failures[0]
