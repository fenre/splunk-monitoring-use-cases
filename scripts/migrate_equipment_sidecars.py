#!/usr/bin/env python3
"""One-time UC sidecar migrations for equipment picker (Phase 0a/0b/0c)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
_CONTENT = _REPO / "content"

_INDUSTRY_STRIP = frozenset(
    {
        "telecom",
        "healthcare",
        "manufacturing",
        "banking",
        "aviation",
        "airport",
        "logistics",
        "retail",
        "insurance",
        "finance",
        "government",
        "education",
        "public_sector",
        "telco",
        "mfg",
        "energy",
        "utilities",
    }
)

# Ingest/platform tokens — not customer equipment.
_NON_EQUIPMENT_STRIP = frozenset(
    {
        "hec",
        "modular_input",
        "kvstore",
        "rest_api",
        "splunk_universal_forwarder",
        "splunk_http_event_collector",
        "splunk_connect",
        "splunk_cloud",
        "splunk_enterprise",
        "splunk_platform",
        "splunk_observability",
        "splunk_on_call",
        "splunk_otel",
        "splunk-db-connect",
        "splunk-mltk",
        "splunk-uba",
        "splunk-ot",
        "index",
        "forwarder",
        "syslog-ng",
        "anthropic",
        "openai",
        "bedrock",
        "azure_openai",
        "passi-auditor-tooling",
    }
)

_GENERIC_SUFFIX = "_generic"


def _load_registry() -> tuple[set[str], set[str]]:
    sys.path.insert(0, str(_REPO / "scripts"))
    sys.path.insert(0, str(_REPO / "tools"))
    from equipment_lib import load_equipment, resolve_equipment_slug  # noqa: E402

    eq_ids: set[str] = set()
    compounds: set[str] = set()
    for entry in load_equipment():
        eq_ids.add(entry["id"])
        for model in entry.get("models") or []:
            compounds.add(f"{entry['id']}_{model['id']}")
    return eq_ids, compounds, resolve_equipment_slug


def _normalize_equipment(
    slugs: list[str],
    valid_eq: set[str],
    resolve,
) -> list[str]:
    out: set[str] = set()
    for slug in slugs:
        if slug in _INDUSTRY_STRIP or slug in _NON_EQUIPMENT_STRIP:
            continue
        canonical = resolve(slug)
        if canonical in valid_eq:
            out.add(canonical)
    return sorted(out)


def _normalize_models(models: list[str], valid_compounds: set[str]) -> list[str]:
    out: set[str] = set()
    for compound in models:
        if compound.endswith(_GENERIC_SUFFIX):
            continue
        if compound in valid_compounds:
            out.add(compound)
    return sorted(out)


def _strip_cim_na(cim_models: list[str] | None) -> list[str] | None:
    if not cim_models:
        return None
    cleaned = [m for m in cim_models if m and m.strip().upper() != "N/A"]
    return cleaned or None


def migrate_sidecar(
    sidecar: dict[str, Any],
    valid_eq: set[str],
    valid_compounds: set[str],
    resolve,
) -> tuple[dict[str, Any], bool]:
    out = dict(sidecar)
    changed = False

    if "cimModels" in out:
        cleaned = _strip_cim_na(out.get("cimModels"))
        if cleaned != out.get("cimModels"):
            changed = True
            if cleaned:
                out["cimModels"] = cleaned
            else:
                out["cimModels"] = []

    if "equipment" in out:
        new_eq = _normalize_equipment(out.get("equipment") or [], valid_eq, resolve)
        if new_eq != sorted(out.get("equipment") or []):
            changed = True
            if new_eq:
                out["equipment"] = new_eq
            else:
                out.pop("equipment", None)

    if "equipmentModels" in out:
        new_models = _normalize_models(out.get("equipmentModels") or [], valid_compounds)
        if new_models != sorted(out.get("equipmentModels") or []):
            changed = True
            if new_models:
                out["equipmentModels"] = new_models
            else:
                out.pop("equipmentModels", None)

    return out, changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)

    valid_eq, valid_compounds, resolve = _load_registry()
    changed_files = 0

    for path in sorted(_CONTENT.rglob("UC-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        new_data, changed = migrate_sidecar(data, valid_eq, valid_compounds, resolve)
        if not changed:
            continue
        changed_files += 1
        if args.write:
            path.write_text(json.dumps(new_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Sidecars changed: {changed_files}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
