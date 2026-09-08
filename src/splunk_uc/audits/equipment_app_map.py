#!/usr/bin/env python3
"""Equipment-to-Splunkbase app map audit (equipment picker Phase 2).

Validates ``data/equipment-app-map.json`` against
``schemas/equipment-app-map.schema.json`` and enforces referential integrity:

* Splunkbase ids resolve in ``data/splunkbase-catalog.json`` (merged with
  overrides) and ``displayName`` matches the catalog entry exactly.
* Equipment slugs resolve in ``EQUIPMENT`` with ``kind=equipment``.
* ``dsaSourceIds`` resolve in ``tools/data-sizing/ot-data-sources.js``.
* Every entry has at least one of ``apps[]`` or ``dsaSourceIds[]``.
* Corroboration: every ``(equipment slug, app id)`` pair must be supported by
  at least one UC sidecar that tags the equipment and references the app.

Run::

    PYTHONPATH=src python3 -m splunk_uc audit-equipment-app-map
    PYTHONPATH=src python3 -m splunk_uc audit-equipment-app-map --check
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO_ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = REPO_ROOT / "data" / "equipment-app-map.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "equipment-app-map.schema.json"
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
OVERRIDES_PATH = REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"
DSA_CATALOGUE = REPO_ROOT / "tools" / "data-sizing" / "ot-data-sources.js"
_SCRIPTS_DIR = REPO_ROOT / "scripts"
_TOOLS_DIR = REPO_ROOT / "tools"

SPLUNKBASE_ID_RE = re.compile(
    r"(?:Splunkbase\s+|splunkbase\.splunk\.com/app/)(\d{2,6})",
    re.IGNORECASE,
)


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_equipment_lib_importable() -> None:
    for directory in (_SCRIPTS_DIR, _TOOLS_DIR):
        if directory.is_dir() and str(directory) not in sys.path:
            sys.path.insert(0, str(directory))


def _load_equipment_slugs() -> dict[str, str]:
    """Return ``slug -> kind`` for every registry entry."""
    _ensure_equipment_lib_importable()
    from equipment_lib import load_equipment  # noqa: WPS433

    return {str(entry["id"]): str(entry.get("kind") or "equipment") for entry in load_equipment()}


def _load_catalog() -> dict[str, dict[str, Any]]:
    """Return merged Splunkbase catalog apps keyed by string id."""
    catalog = _load_json(CATALOG_PATH)
    overrides = _load_json(OVERRIDES_PATH) if OVERRIDES_PATH.is_file() else {}
    apps: dict[str, dict[str, Any]] = {}
    for key, entry in (catalog.get("apps") or {}).items():
        if isinstance(entry, dict):
            apps[str(key)] = dict(entry)
    for key, entry in (overrides.get("apps") or {}).items():
        if not isinstance(entry, dict):
            continue
        if str(key) in apps:
            apps[str(key)].update(entry)
        else:
            apps[str(key)] = dict(entry)
    return apps


def _load_dsa_source_ids() -> set[str]:
    """Extract ``OT_DATA_SOURCES[].id`` values from the DSA catalogue."""
    if not DSA_CATALOGUE.is_file():
        raise FileNotFoundError(f"DSA catalogue not found: {DSA_CATALOGUE}")
    proc = subprocess.run(
        [
            "node",
            "-e",
            "global.window = {};"
            f"require({json.dumps(str(DSA_CATALOGUE))});"
            "process.stdout.write(JSON.stringify("
            "global.window.OT_DATA_SOURCES.map((s) => s.id)));",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    if not isinstance(payload, list):
        raise ValueError("OT_DATA_SOURCES did not parse to a list")
    return {str(item) for item in payload}


def _validate_schema(document: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:  # pragma: no cover - dev dependency
        raise SystemExit(
            f"[equipment-app-map] missing dev dependency 'jsonschema': {exc}"
        ) from exc

    schema = _load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    return [
        f"schema: {'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def _extract_uc_app_ids(payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for field in ("app", "dataSources", "implementation", "detailedImplementation"):
        text = payload.get(field)
        if isinstance(text, str) and text:
            for match in SPLUNKBASE_ID_RE.finditer(text):
                ids.add(match.group(1))
    for entry in payload.get("splunkbaseApps") or []:
        if isinstance(entry, dict) and entry.get("id") is not None:
            ids.add(str(entry["id"]))
    return ids


def build_corroboration_index() -> Counter[tuple[str, str]]:
    """Count UC sidecars that tag an equipment slug and reference a Splunkbase app."""
    counts: Counter[tuple[str, str]] = Counter()
    for _path, payload in iter_uc_sidecars():
        equipment = {
            slug.strip()
            for slug in (payload.get("equipment") or [])
            if isinstance(slug, str) and slug.strip()
        }
        if not equipment:
            continue
        app_ids = _extract_uc_app_ids(payload)
        if not app_ids:
            continue
        for slug in equipment:
            for app_id in app_ids:
                counts[(slug, app_id)] += 1
    return counts


def audit_map(
    document: dict[str, Any],
    *,
    catalog: dict[str, dict[str, Any]],
    equipment_kinds: dict[str, str],
    dsa_ids: set[str],
    corroboration: Counter[tuple[str, str]],
) -> list[str]:
    errors: list[str] = []
    entries = document.get("entries")
    if not isinstance(entries, dict):
        return ["entries: expected object keyed by equipment slug"]

    for slug, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            errors.append(f"{slug}: entry must be an object")
            continue

        kind = equipment_kinds.get(slug)
        if kind is None:
            errors.append(f"{slug}: unknown equipment slug (not in EQUIPMENT registry)")
            continue
        if kind != "equipment":
            errors.append(
                f"{slug}: registry kind is {kind!r}; only kind=equipment is permitted"
            )

        apps = entry.get("apps") or []
        dsa_source_ids = entry.get("dsaSourceIds") or []
        if not apps and not dsa_source_ids:
            errors.append(f"{slug}: requires at least one app or dsaSourceId")

        for dsa_id in dsa_source_ids:
            if dsa_id not in dsa_ids:
                errors.append(f"{slug}: unknown dsaSourceId {dsa_id!r}")

        for app in apps:
            if not isinstance(app, dict):
                errors.append(f"{slug}: apps[] entries must be objects")
                continue
            app_id = str(app.get("id", ""))
            display_name = app.get("displayName")
            catalog_entry = catalog.get(app_id)
            if catalog_entry is None:
                errors.append(f"{slug}: Splunkbase app id {app_id!r} not in catalog")
                continue
            catalog_name = catalog_entry.get("displayName")
            if display_name != catalog_name:
                errors.append(
                    f"{slug}: app {app_id!r} displayName {display_name!r} "
                    f"!= catalog {catalog_name!r}"
                )
            if corroboration.get((slug, app_id), 0) == 0:
                errors.append(
                    f"{slug}: zero UC support for app {app_id!r} "
                    f"({display_name!r}) pairing"
                )

    return errors


def run_audit() -> list[str]:
    document = _load_json(MAP_PATH)
    errors = _validate_schema(document)
    if errors:
        return errors

    catalog = _load_catalog()
    equipment_kinds = _load_equipment_slugs()
    dsa_ids = _load_dsa_source_ids()
    corroboration = build_corroboration_index()
    errors.extend(
        audit_map(
            document,
            catalog=catalog,
            equipment_kinds=equipment_kinds,
            dsa_ids=dsa_ids,
            corroboration=corroboration,
        )
    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit data/equipment-app-map.json (equipment picker Phase 2).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit non-zero when validation fails.",
    )
    args = parser.parse_args(argv)

    try:
        errors = run_audit()
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"[equipment-app-map] ERROR: {exc}", file=sys.stderr)
        return 2

    entries = (_load_json(MAP_PATH).get("entries") or {}) if MAP_PATH.is_file() else {}
    print("=" * 72)
    print("Equipment app map audit (data/equipment-app-map.json)")
    print("=" * 72)
    print(f"Mapped equipment slugs: {len(entries)}")
    print(f"Errors: {len(errors)}")

    if errors:
        print("\nFAILURES:")
        print("-" * 72)
        for err in errors:
            print(f"  - {err}")

    if errors and args.check:
        return 1
    if not errors:
        print("\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
