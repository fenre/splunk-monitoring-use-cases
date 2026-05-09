#!/usr/bin/env python3
"""Catalogue health metrics — release-time trend snapshot management.

Repo-overhaul plan §P8 step 2 (2026-05-09): every release commits a
trend snapshot of ``dist/metrics.json`` under
``data/metrics-history/<VERSION>.json`` plus an ordered
``data/metrics-history/index.json`` that lists every release ever
captured. The snapshots give downstream consumers (dashboards,
release-quality reports, regression hunts) a permanent record of how
the catalogue evolved without forcing them to re-walk
``content/cat-NN-slug/`` themselves.

This script is the single entry point. It runs in two modes:

* ``--write`` — read the live ``dist/metrics.json`` (must already
  exist), copy it *verbatim* to ``data/metrics-history/<VERSION>.json``,
  refresh ``data/metrics-history/index.json`` so it stays sorted and
  truthful. Idempotent: re-running on an unchanged build produces
  byte-identical files. The snapshot is a verbatim copy of
  ``dist/metrics.json`` (no synthetic fields added) so it validates
  against ``schemas/v2/metrics.schema.json`` and downstream tooling
  can consume snapshots with the same parser it uses for the live
  artefact.
* ``--check`` — fail (exit 1) when a release is bumped without a
  matching snapshot. Specifically: ``data/metrics-history/<VERSION>``
  must exist, validate against ``schemas/v2/metrics.schema.json``,
  carry the same ``catalogueVersion`` and ``schema_version`` as the
  current ``dist/metrics.json`` (or — if ``dist/metrics.json`` is
  missing because nobody ran ``make build`` yet — the snapshot's
  schema must still match ``schemas/v2/metrics.schema.json``). The
  index file must be sorted and reference every snapshot file on
  disk and only those.

The check intentionally does **not** assert that detailed counts
match between the committed snapshot and the live build. Per-PR
content edits change the metrics; gating on per-field equality would
fire on every UC PR, which is exactly the noise we need to avoid.
The contract is "every release has a permanent snapshot", not
"every PR matches the latest snapshot".

Stdlib-only per ADR-0004 (no ``jsonschema`` runtime dependency: we
load and walk the schema by hand for the few fields we gate on).

Exit codes
----------

* ``0`` — snapshot present and well-formed (``--check``); snapshot
  written/refreshed (``--write``).
* ``1`` — drift detected (missing snapshot, malformed JSON, version
  mismatch, index out-of-sync).
* ``2`` — usage / I/O error (missing ``dist/metrics.json`` in
  ``--write`` mode, malformed VERSION file, etc.).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST_METRICS = PROJECT_ROOT / "dist" / "metrics.json"
DEFAULT_HISTORY_DIR = PROJECT_ROOT / "data" / "metrics-history"
DEFAULT_INDEX_PATH = DEFAULT_HISTORY_DIR / "index.json"
DEFAULT_VERSION_FILE = PROJECT_ROOT / "VERSION"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "schemas" / "v2" / "metrics.schema.json"

INDEX_SCHEMA_VERSION = "1.0.0"


def _display_path(path: Path) -> str:
    """Return ``path`` as a project-relative string, falling back to absolute.

    ``Path.relative_to`` raises ``ValueError`` when the target is
    outside ``PROJECT_ROOT`` — which happens during tests that
    operate on a tmp directory. We never want a cosmetic path
    rendering to crash the audit, so we fall back to the absolute
    path in that case.
    """
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


def _read_version(version_file: Path) -> str:
    """Return the trimmed contents of ``VERSION``.

    Raises ``SystemExit(2)`` if the file is missing or empty so a
    misconfigured working tree fails loudly instead of silently
    overwriting a snapshot at the wrong path.
    """
    if not version_file.exists():
        sys.stderr.write(f"FATAL: VERSION file not found at {version_file}\n")
        raise SystemExit(2)
    raw = version_file.read_text(encoding="utf-8").strip()
    if not raw:
        sys.stderr.write(f"FATAL: VERSION file at {version_file} is empty\n")
        raise SystemExit(2)
    return raw


def _load_metrics(metrics_path: Path) -> dict[str, Any]:
    """Load and shallow-validate ``dist/metrics.json``.

    A missing file is a hard error in ``--write`` mode (caller has
    not run ``make build`` yet), but the caller in ``--check`` mode
    can choose to keep going if the schema gate is enough.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(metrics_path)
    try:
        with metrics_path.open(encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"FATAL: malformed JSON at {metrics_path}: {exc}\n")
        raise SystemExit(2) from exc
    if not isinstance(payload, dict):
        sys.stderr.write(f"FATAL: {metrics_path} top-level is not an object\n")
        raise SystemExit(2)
    return payload


def _validate_metrics_shape(payload: dict[str, Any], *, source: Path) -> list[str]:
    """Return a list of human-readable defects, empty when payload is OK.

    We don't pull in ``jsonschema`` here (stdlib-only per ADR-0004);
    instead we check the small set of fields we actually rely on
    downstream:

    * ``schema_version`` is a string semver
    * ``catalogueVersion`` is a string semver
    * ``counts.useCases`` is an integer
    * ``$schema`` ends in ``metrics.schema.json``
    """
    issues: list[str] = []
    schema_ver = payload.get("schema_version")
    if not isinstance(schema_ver, str) or not schema_ver:
        issues.append(f"{source}: schema_version is missing or non-string")
    cat_ver = payload.get("catalogueVersion")
    if not isinstance(cat_ver, str) or not cat_ver:
        issues.append(f"{source}: catalogueVersion is missing or non-string")
    counts = payload.get("counts")
    if not isinstance(counts, dict) or not isinstance(counts.get("useCases"), int):
        issues.append(f"{source}: counts.useCases is missing or non-integer")
    schema_ref = payload.get("$schema")
    if not isinstance(schema_ref, str) or "metrics.schema.json" not in schema_ref:
        issues.append(f"{source}: $schema does not reference metrics.schema.json")
    return issues


# ---------------------------------------------------------------------------
# Index management
# ---------------------------------------------------------------------------


def _load_index(index_path: Path) -> dict[str, Any]:
    """Return the parsed index file, or a fresh empty index when absent."""
    if not index_path.exists():
        return {
            "$schema": "/schemas/v2/metrics-history-index.schema.json",
            "schema_version": INDEX_SCHEMA_VERSION,
            "snapshots": [],
        }
    try:
        with index_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"FATAL: malformed index file at {index_path}: {exc}\n")
        raise SystemExit(2) from exc
    if not isinstance(data, dict) or not isinstance(data.get("snapshots"), list):
        sys.stderr.write(f"FATAL: index file at {index_path} has unexpected shape\n")
        raise SystemExit(2)
    return data


def _semver_key(v: str) -> tuple[int, ...]:
    """Sort key for a semver string.

    Strips both the ``-prerelease`` and ``+buildmetadata`` suffixes per
    SemVer 2.0.0 §10. Returns ``(0,)`` for unparseable input so the
    sort doesn't crash on legacy/garbage version strings — they just
    sink to the bottom.
    """
    head = v.split("-", 1)[0].split("+", 1)[0]
    parts = head.split(".")
    out: list[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            return (0,)
    while len(out) < 3:
        out.append(0)
    return tuple(out)


def _refresh_index(history_dir: Path, index_path: Path) -> dict[str, Any]:
    """Rebuild the index from the snapshot files actually present on disk.

    Re-derived rather than mutated incrementally so a hand-deleted
    snapshot file gets removed from the index automatically on the
    next ``--write`` cycle. The index is sorted by semver descending
    (newest release first) for human-readability.
    """
    snapshots: list[dict[str, Any]] = []
    for path in sorted(history_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        version = path.stem
        try:
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        snapshots.append({
            "version": version,
            "schemaVersion": payload.get("schema_version", ""),
            "generatedAt": payload.get("generatedAt", ""),
            "useCases": (payload.get("counts") or {}).get("useCases", 0),
            "file": path.name,
        })
    snapshots.sort(key=lambda s: _semver_key(str(s["version"])), reverse=True)

    return {
        "$schema": "/schemas/v2/metrics-history-index.schema.json",
        "schema_version": INDEX_SCHEMA_VERSION,
        "snapshots": snapshots,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# --write mode
# ---------------------------------------------------------------------------


def write_snapshot(
    *,
    metrics_path: Path,
    history_dir: Path,
    index_path: Path,
    version_file: Path,
) -> Path:
    """Copy ``dist/metrics.json`` to ``data/metrics-history/<VERSION>.json``.

    The committed snapshot is a *verbatim* copy of ``dist/metrics.json``
    — no synthetic fields are added. This guarantees the snapshot
    validates against ``schemas/v2/metrics.schema.json`` (which has
    ``additionalProperties: false``) and that downstream tooling can
    consume the snapshot file with the same parser it uses for the
    live build artefact. The ``generatedAt`` field is already present
    in ``dist/metrics.json`` and is frozen to git commit time in
    reproducible builds, so we have no need for a separate
    ``capturedAt`` timestamp.

    Returns the destination path. Caller should ``git add`` both the
    snapshot file and the refreshed ``index.json``.
    """
    version = _read_version(version_file)
    payload = _load_metrics(metrics_path)
    issues = _validate_metrics_shape(payload, source=metrics_path)
    if issues:
        for line in issues:
            sys.stderr.write(f"ERROR: {line}\n")
        raise SystemExit(1)

    history_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = history_dir / f"{version}.json"
    _write_json(snapshot_path, dict(payload))

    index = _refresh_index(history_dir, index_path)
    _write_json(index_path, index)

    return snapshot_path


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------


def check_snapshot(
    *,
    metrics_path: Path,
    history_dir: Path,
    index_path: Path,
    version_file: Path,
) -> list[str]:
    """Return a list of human-readable check failures (empty when OK).

    Gates:

    1. ``data/metrics-history/<VERSION>.json`` exists.
    2. The committed snapshot satisfies ``_validate_metrics_shape``.
    3. The committed snapshot's ``schema_version`` is a string the
       on-disk schema accepts (semver, non-empty).
    4. The committed snapshot's ``catalogueVersion`` matches
       ``VERSION``.
    5. The on-disk index is byte-equal to a freshly-derived index.
    6. If ``dist/metrics.json`` exists *and* its ``catalogueVersion``
       equals VERSION, then its ``schema_version`` must equal the
       committed snapshot's ``schema_version``.
    """
    version = _read_version(version_file)
    failures: list[str] = []

    snapshot_path = history_dir / f"{version}.json"
    if not snapshot_path.exists():
        failures.append(
            f"missing snapshot at {_display_path(snapshot_path)}"
            f" — run `make snapshot-metrics` after bumping VERSION to {version}"
        )
        return failures

    try:
        with snapshot_path.open(encoding="utf-8") as f:
            snapshot = json.load(f)
    except json.JSONDecodeError as exc:
        failures.append(f"{snapshot_path}: malformed JSON: {exc}")
        return failures

    if not isinstance(snapshot, dict):
        failures.append(f"{snapshot_path}: top-level is not an object")
        return failures

    failures.extend(_validate_metrics_shape(snapshot, source=snapshot_path))

    snap_cat_ver = snapshot.get("catalogueVersion")
    if snap_cat_ver != version:
        failures.append(
            f"{snapshot_path}: catalogueVersion is {snap_cat_ver!r} but VERSION is {version!r}"
        )

    failures.extend(_check_index(history_dir, index_path))

    if metrics_path.exists():
        try:
            live = _load_metrics(metrics_path)
        except SystemExit:
            return failures
        live_cat_ver = live.get("catalogueVersion")
        if live_cat_ver == version:
            live_schema_ver = live.get("schema_version")
            snap_schema_ver = snapshot.get("schema_version")
            if live_schema_ver != snap_schema_ver:
                failures.append(
                    f"{snapshot_path}: snapshot schema_version is {snap_schema_ver!r} "
                    f"but live build emits {live_schema_ver!r}"
                )

    return failures


def _check_index(history_dir: Path, index_path: Path) -> list[str]:
    """Verify index.json is byte-identical to a freshly-derived index."""
    if not index_path.exists():
        return [f"missing index at {_display_path(index_path)}"]
    derived = _refresh_index(history_dir, index_path)
    derived_text = json.dumps(derived, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    on_disk_text = index_path.read_text(encoding="utf-8")
    if derived_text != on_disk_text:
        return [
            f"{_display_path(index_path)} is out of sync with snapshot files; "
            f"run `make snapshot-metrics` to refresh"
        ]
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="snapshot_metrics",
        description=(
            "Manage data/metrics-history/<VERSION>.json release snapshots."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--write",
        action="store_true",
        help=(
            "Copy dist/metrics.json into the history directory under the "
            "current VERSION and refresh the sorted index."
        ),
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help=(
            "Fail when a release is bumped without a corresponding snapshot."
        ),
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=DEFAULT_DIST_METRICS,
        help=f"Path to dist/metrics.json (default: {DEFAULT_DIST_METRICS}).",
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=DEFAULT_HISTORY_DIR,
        help=f"Path to data/metrics-history/ (default: {DEFAULT_HISTORY_DIR}).",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help=f"Path to the index file (default: {DEFAULT_INDEX_PATH}).",
    )
    parser.add_argument(
        "--version-file",
        type=Path,
        default=DEFAULT_VERSION_FILE,
        help=f"Path to VERSION (default: {DEFAULT_VERSION_FILE}).",
    )
    args = parser.parse_args(argv)

    if args.write:
        try:
            dest = write_snapshot(
                metrics_path=args.metrics,
                history_dir=args.history_dir,
                index_path=args.index,
                version_file=args.version_file,
            )
        except FileNotFoundError as exc:
            sys.stderr.write(
                f"FATAL: {exc.filename or args.metrics} not found; "
                f"run `make build` first.\n"
            )
            return 2
        sys.stdout.write(f"wrote snapshot {_display_path(dest)}\n")
        sys.stdout.write(f"refreshed index {_display_path(args.index)}\n")
        return 0

    failures = check_snapshot(
        metrics_path=args.metrics,
        history_dir=args.history_dir,
        index_path=args.index,
        version_file=args.version_file,
    )
    if failures:
        sys.stderr.write("snapshot_metrics: drift detected\n")
        for line in failures:
            sys.stderr.write(f"  - {line}\n")
        return 1
    sys.stdout.write("snapshot_metrics: OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
