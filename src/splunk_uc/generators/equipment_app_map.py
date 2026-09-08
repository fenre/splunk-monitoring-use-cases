#!/usr/bin/env python3
"""Equipment picker Phase 5 — curated equipment slug → Splunkbase app map.

Builds ``data/equipment-app-map.json`` for every registry entry with
``kind=equipment`` (~127 slugs). For each slug the generator:

* Matches ``SPLUNK_TAS`` / ``SPLUNK_APPS`` from ``tools/build/enrichment.py``
  against the equipment's ``tas`` patterns.
* Pulls ``dsaSourceIds`` from ``tools/data-sizing/mapping.js``
  (``DSA_EQUIPMENT_MAP``).
* Keeps only Splunkbase app ids that UC sidecars corroborate (equipment tag
  + Splunkbase reference in the same sidecar). When no app is corroborated,
  emits an ingest-only entry (``dsaSourceIds`` only).

Gated by ``python3 -m splunk_uc audit-equipment-app-map --check``.

USAGE:
    python3 -m splunk_uc generate-equipment-app-map
    python3 -m splunk_uc generate-equipment-app-map --check
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from splunk_uc.audits._uc_walk import iter_uc_sidecars

REPO_ROOT = Path(__file__).resolve().parents[3]
MAP_PATH = REPO_ROOT / "data" / "equipment-app-map.json"
ENRICHMENT_PATH = REPO_ROOT / "tools" / "build" / "enrichment.py"
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
OVERRIDES_PATH = REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"
DSA_MAPPING = REPO_ROOT / "tools" / "data-sizing" / "mapping.js"
_SCHEMA_REF = "../schemas/equipment-app-map.schema.json"

SPLUNKBASE_ID_RE = re.compile(
    r"(?:Splunkbase\s+|splunkbase\.splunk\.com/app/)(\d{2,6})",
    re.IGNORECASE,
)

# Slugs absent from DSA_EQUIPMENT_MAP but still needing ingest-only coverage.
_DSA_FALLBACK: dict[str, list[str]] = {
    "alibaba": ["dsa_it_cloud_iaas"],
    "openshift": ["dsa_it_cloud_iaas"],
}

_PREMIUM_APP_IDS = frozenset({"2686"})
_OPTIONAL_APP_IDS = frozenset({"2686", "5709"})


def _deterministic_timestamp() -> str:
    """Stable UTC timestamp for committed map files."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    sde = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if sde.isdigit():
        return time.strftime(fmt, time.gmtime(int(sde)))
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--pretty=%ct", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        ts = out.stdout.strip()
        if ts.isdigit():
            return time.strftime(fmt, time.gmtime(int(ts)))
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return time.strftime(fmt, time.gmtime())


def _load_enrichment_module() -> Any:
    spec = importlib.util.spec_from_file_location("enrichment", ENRICHMENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load enrichment module from {ENRICHMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_catalog() -> dict[str, dict[str, Any]]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    overrides = (
        json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        if OVERRIDES_PATH.is_file()
        else {}
    )
    merged: dict[str, dict[str, Any]] = {}
    for key, entry in (catalog.get("apps") or {}).items():
        if isinstance(entry, dict):
            merged[str(key)] = dict(entry)
    for key, entry in (overrides.get("apps") or {}).items():
        if not isinstance(entry, dict):
            continue
        sid = str(key)
        if sid in merged:
            merged[sid].update(entry)
        else:
            merged[sid] = dict(entry)
    return merged


def _load_dsa_equipment_map() -> dict[str, list[str]]:
    proc = subprocess.run(
        [
            "node",
            "-e",
            "global.window = {};"
            f"require({json.dumps(str(DSA_MAPPING))});"
            "process.stdout.write(JSON.stringify(window.DSA_EQUIPMENT_MAP));",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(REPO_ROOT),
    )
    payload = json.loads(proc.stdout)
    if not isinstance(payload, dict):
        raise ValueError("DSA_EQUIPMENT_MAP did not parse to an object")
    out: dict[str, list[str]] = {}
    for slug, ids in payload.items():
        if isinstance(slug, str) and isinstance(ids, list):
            out[slug] = [str(item) for item in ids if isinstance(item, str) and item]
    return out


def _equipment_patterns(eq: dict[str, Any]) -> list[str]:
    patterns = [str(p).lower() for p in eq.get("tas") or []]
    for model in eq.get("models") or []:
        if isinstance(model, dict):
            patterns.extend(str(p).lower() for p in model.get("tas") or [])
    return patterns


def _pattern_matches_enrichment(patterns: Iterable[str], enrichment_patterns: Iterable[str]) -> bool:
    for ep in patterns:
        for needle in enrichment_patterns:
            nl = str(needle).lower()
            if nl in ep or ep in nl:
                return True
    return False


def _enrichment_app_ids(eq: dict[str, Any], enrichment: Any) -> set[str]:
    patterns = _equipment_patterns(eq)
    matched: set[str] = set()
    for ta in enrichment.SPLUNK_TAS:
        if _pattern_matches_enrichment(patterns, ta.get("tas") or []):
            matched.add(str(ta["id"]))
    for app in enrichment.SPLUNK_APPS:
        if _pattern_matches_enrichment(patterns, app.get("tas") or []):
            matched.add(str(app["id"]))
    return matched


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


def _dsa_source_ids(slug: str, dsa_map: dict[str, list[str]]) -> list[str]:
    ids = list(dict.fromkeys(dsa_map.get(slug) or _DSA_FALLBACK.get(slug, [])))
    return ids


def _build_app_refs(
    corroborated_ids: list[str],
    catalog: dict[str, dict[str, Any]],
    enrichment: Any,
) -> list[dict[str, Any]]:
    ta_by_id = {str(t["id"]): t for t in enrichment.SPLUNK_TAS}
    app_by_id = {str(a["id"]): a for a in enrichment.SPLUNK_APPS}

    primary_id = None
    for ta in enrichment.SPLUNK_TAS:
        tid = str(ta["id"])
        if tid in corroborated_ids:
            primary_id = tid
            break
    if primary_id is None:
        primary_id = corroborated_ids[0]

    apps: list[dict[str, Any]] = []
    for app_id in corroborated_ids:
        catalog_entry = catalog[app_id]
        role = "primary" if app_id == primary_id else "data-source"
        if app_id in app_by_id and app_id != primary_id:
            role = "data-source"
        if app_id in _OPTIONAL_APP_IDS:
            role = "optional"
        premium = app_id in _PREMIUM_APP_IDS or bool(catalog_entry.get("premium"))
        apps.append(
            {
                "id": app_id,
                "displayName": catalog_entry["displayName"],
                "role": role,
                "premium": premium,
            }
        )
    return apps


def generate_map() -> dict[str, Any]:
    enrichment = _load_enrichment_module()
    catalog = _load_catalog()
    dsa_map = _load_dsa_equipment_map()
    corroboration = build_corroboration_index()

    equipment = sorted(
        (entry for entry in enrichment.EQUIPMENT if entry.get("kind") == "equipment"),
        key=lambda item: item["id"],
    )

    entries: dict[str, dict[str, Any]] = {}
    for eq in equipment:
        slug = str(eq["id"])
        candidate_ids = _enrichment_app_ids(eq, enrichment)
        candidate_ids.update(
            app_id
            for (eq_slug, app_id), _count in corroboration.items()
            if eq_slug == slug
        )
        corroborated_ids = sorted(
            app_id
            for app_id in candidate_ids
            if corroboration.get((slug, app_id), 0) > 0 and app_id in catalog
        )
        dsa_ids = _dsa_source_ids(slug, dsa_map)

        entry: dict[str, Any] = {}
        if corroborated_ids:
            entry["apps"] = _build_app_refs(corroborated_ids, catalog, enrichment)
        if dsa_ids:
            entry["dsaSourceIds"] = dsa_ids
        if not entry.get("apps") and not entry.get("dsaSourceIds"):
            raise RuntimeError(
                f"{slug}: no corroborated Splunkbase apps and no DSA source ids"
            )
        entries[slug] = entry

    return {
        "$schema": _SCHEMA_REF,
        "version": "1.0.0",
        "generatedAt": _deterministic_timestamp(),
        "entries": entries,
    }


def _canonical_json(document: dict[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate data/equipment-app-map.json (equipment picker Phase 5).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode: exit 1 when the committed map drifts from generator output.",
    )
    args = parser.parse_args(argv)

    try:
        generated = generate_map()
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"[generate-equipment-app-map] ERROR: {exc}", file=sys.stderr)
        return 2

    rendered = _canonical_json(generated)
    if args.check:
        if not MAP_PATH.is_file():
            print(f"[generate-equipment-app-map] missing {MAP_PATH}", file=sys.stderr)
            return 1
        committed = MAP_PATH.read_text(encoding="utf-8")
        if committed != rendered:
            print(
                "[generate-equipment-app-map] drift: "
                f"run `python3 -m splunk_uc generate-equipment-app-map`",
                file=sys.stderr,
            )
            return 1
        print(f"[generate-equipment-app-map] OK ({len(generated['entries'])} entries)")
        return 0

    MAP_PATH.write_text(rendered, encoding="utf-8")
    print(
        f"[generate-equipment-app-map] wrote {MAP_PATH} "
        f"({len(generated['entries'])} entries)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
