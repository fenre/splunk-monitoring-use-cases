#!/usr/bin/env python3
"""Validate tools/data-sizing/ot-data-sources.js against the v2 schema.

Checks performed:
  1. Schema validation of every source object.
  2. Every `compute` reference resolves in compute-functions.js.
  3. Every `id` is unique.
  4. Every `related_uc_ids` entry resolves in catalog.json.

Exit non-zero on any failure. Designed for CI use.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[3]
TOOL = REPO / "tools" / "data-sizing"
SCHEMA = TOOL / "schemas" / "data-source.schema.json"
CATALOGUE = TOOL / "ot-data-sources.js"
COMPUTE = TOOL / "compute-functions.js"
CATALOG_JSON = REPO / "catalog.json"


def extract_catalogue() -> list:
    """Extract OT_DATA_SOURCES via a Node one-liner (same pattern as
    non-technical-view.js validation elsewhere in the repo)."""
    proc = subprocess.run(
        ["node", "-e",
         "global.window = {};"
         f"require({json.dumps(str(CATALOGUE))});"
         "process.stdout.write(JSON.stringify(global.window.OT_DATA_SOURCES));"],
        capture_output=True, check=True, text=True,
    )
    return json.loads(proc.stdout)


def extract_compute_names() -> set[str]:
    """Find all top-level COMPUTE function names by regex."""
    text = COMPUTE.read_text(encoding="utf-8")
    return set(re.findall(r"\bfunction\s+([a-z0-9_]+_v\d+)\s*\(", text))


def known_uc_ids() -> set[str]:
    """Load UC IDs from the published catalog.json (built artefact)."""
    if not CATALOG_JSON.exists():
        # In a fresh checkout `make build` hasn't run; skip the UC check
        # rather than failing CI.
        return set()
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    return {
        uc["i"]
        for cat in data["DATA"]
        for sub in cat.get("s", [])
        for uc in sub.get("u", [])
    }


def main() -> int:
    sources = extract_catalogue()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    failures: list[str] = []

    # 1. Schema validation per source.
    for s in sources:
        errs = list(validator.iter_errors(s))
        for e in errs:
            failures.append(f"[{s.get('id', '<no-id>')}] schema: {e.message}")

    # 2. Compute references resolve.
    compute_names = extract_compute_names()
    for s in sources:
        if s.get("compute") and s["compute"] not in compute_names:
            failures.append(f"[{s['id']}] compute reference '{s['compute']}' "
                            f"not found in compute-functions.js")

    # 3. Unique IDs.
    seen: dict[str, int] = {}
    for s in sources:
        sid = s.get("id")
        if not sid:
            continue
        seen[sid] = seen.get(sid, 0) + 1
    for sid, count in seen.items():
        if count > 1:
            failures.append(f"duplicate id: {sid} ({count} entries)")

    # 4. related_uc_ids resolve in catalog.json (if available).
    valid_ucs = known_uc_ids()
    if valid_ucs:
        for s in sources:
            for uc in s.get("related_uc_ids") or []:
                if uc not in valid_ucs:
                    failures.append(f"[{s['id']}] related_uc_ids '{uc}' "
                                    f"does not exist in catalog.json")

    if failures:
        print(f"FAIL: {len(failures)} validation errors:")
        for f in failures[:50]:
            print(f"  - {f}")
        if len(failures) > 50:
            print(f"  ... and {len(failures) - 50} more")
        return 1

    print(f"PASS: {len(sources)} sources validate against the v2 schema.")
    print(f"      {len(compute_names)} compute functions registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
