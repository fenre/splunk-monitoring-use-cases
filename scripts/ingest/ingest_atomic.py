#!/usr/bin/env python3
"""Production ingest: Red Canary Atomic Red Team test catalogue.

Source: https://github.com/redcanaryco/atomic-red-team (master branch).

The driver:
  1. Downloads the master ``atomics/Indexes/index.yaml`` to
     ``vendor/atomic-red-team/index.yaml``. This single file (~6.6 MB)
     contains every atomic test indexed by ATT&CK tactic/technique.
  2. Records SHA-256 + HTTP metadata in the shared manifest.
  3. Normalises the YAML into two flat JSON files under
     ``data/crosswalks/atomic-red-team/``:
       * ``atomics.normalised.json``    - one row per atomic test with the
         ATT&CK technique_id, platforms, executor type, and an ATT&CK URL.
       * ``techniques.normalised.json`` - aggregate counts per technique.

Run:
  .venv-feasibility/bin/python scripts/ingest/ingest_atomic.py

Exits 0 on success, non-zero on any fetch / normalisation failure.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any, Dict, List, Tuple

import yaml  # type: ignore

_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from manifest import FetchRecord, fetch, merge_into_manifest  # noqa: E402

MANIFEST_PATH = _REPO / "data" / "provenance" / "ingest-manifest.json"
VENDOR_DIR = _REPO / "vendor" / "atomic-red-team"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "atomic-red-team"

SOURCE = {
    "id": "atomic-red-team-index",
    "url": "https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/Indexes/index.yaml",
    "local": VENDOR_DIR / "index.yaml",
}

_TECHNIQUE_RE = re.compile(r"^T\d{4}(?:\.\d{3})?$")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _first_line(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _attack_url(technique_id: str) -> str:
    if "." in technique_id:
        parent, sub = technique_id.split(".", 1)
        return f"https://attack.mitre.org/techniques/{parent}/{sub}/"
    return f"https://attack.mitre.org/techniques/{technique_id}/"


def _walk_technique_block(block: Any) -> Tuple[Dict, List[Dict]]:
    """Return ``(technique_meta, atomic_tests)`` from a technique-level block.

    The index format nests either a raw ``atomic_tests`` list directly under
    the technique key, or under a ``technique`` subdocument.
    """

    if not isinstance(block, dict):
        return {}, []
    technique_meta = block.get("technique") if isinstance(block.get("technique"), dict) else {}
    atomic_tests = _as_list(block.get("atomic_tests"))
    return technique_meta, atomic_tests


def _normalise(doc: Any) -> Dict:
    atomics: List[Dict] = []
    per_technique: Dict[str, Dict] = {}

    if not isinstance(doc, dict):
        raise ValueError("Atomic Red Team index.yaml did not parse as a mapping")

    for tactic_name, techniques in doc.items():
        if not isinstance(techniques, dict):
            continue
        for technique_id, block in techniques.items():
            tid = str(technique_id).strip()
            if not _TECHNIQUE_RE.match(tid):
                continue
            technique_meta, tests = _walk_technique_block(block)
            technique_name = str(technique_meta.get("name") or "").strip()
            is_sub = bool(technique_meta.get("x_mitre_is_subtechnique", False))
            technique_entry = per_technique.setdefault(
                tid,
                {
                    "attack_id": tid,
                    "name": technique_name,
                    "is_subtechnique": is_sub,
                    "url": _attack_url(tid),
                    "tactics": [],
                    "atomic_count": 0,
                    "platforms": set(),
                },
            )
            if technique_name and not technique_entry["name"]:
                technique_entry["name"] = technique_name
            if tactic_name not in technique_entry["tactics"]:
                technique_entry["tactics"].append(tactic_name)
            for test in tests:
                if not isinstance(test, dict):
                    continue
                platforms = [str(p).strip().lower() for p in _as_list(test.get("supported_platforms")) if p]
                technique_entry["platforms"].update(platforms)
                executor = test.get("executor") if isinstance(test.get("executor"), dict) else {}
                executor_type = str(executor.get("name") or "").strip().lower()
                atomics.append(
                    {
                        "attack_id": tid,
                        "technique_name": technique_name,
                        "tactic": tactic_name,
                        "test_name": test.get("name"),
                        "guid": test.get("auto_generated_guid"),
                        "description": _first_line(test.get("description")),
                        "platforms": platforms,
                        "executor": executor_type,
                        "elevation_required": bool(test.get("elevation_required", False)),
                        "has_cleanup": bool(isinstance(executor, dict) and executor.get("cleanup_command")),
                        "url": _attack_url(tid),
                    }
                )
                technique_entry["atomic_count"] += 1

    techniques_list: List[Dict] = []
    for entry in per_technique.values():
        entry["platforms"] = sorted(entry["platforms"])
        entry["tactics"] = sorted(entry["tactics"])
        techniques_list.append(entry)

    techniques_list.sort(key=lambda t: t["attack_id"])
    atomics.sort(key=lambda t: (t["attack_id"], str(t["test_name"] or "")))

    return {
        "source": "atomic-red-team-index",
        "techniques_count": len(techniques_list),
        "atomics_count": len(atomics),
        "techniques": techniques_list,
        "atomics": atomics,
    }


def run() -> int:
    CROSSWALK_DIR.mkdir(parents=True, exist_ok=True)

    print(f"- fetching {SOURCE['id']} ...", flush=True)
    try:
        rec: FetchRecord = fetch(
            source_id=SOURCE["id"],
            url=SOURCE["url"],
            dest=SOURCE["local"],
            repo_root=_REPO,
        )
    except Exception as err:
        print(f"  FAIL: {err}", file=sys.stderr)
        return 2

    with SOURCE["local"].open("r", encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)

    normalised = _normalise(doc)

    atomics_path = CROSSWALK_DIR / "atomics.normalised.json"
    techniques_path = CROSSWALK_DIR / "techniques.normalised.json"

    atomics_path.write_text(
        json.dumps(
            {
                "source": normalised["source"],
                "atomics_count": normalised["atomics_count"],
                "atomics": normalised["atomics"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    techniques_path.write_text(
        json.dumps(
            {
                "source": normalised["source"],
                "techniques_count": normalised["techniques_count"],
                "techniques": normalised["techniques"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "  ok:",
        f"techniques={normalised['techniques_count']}",
        f"atomics={normalised['atomics_count']}",
    )

    merge_into_manifest(MANIFEST_PATH, [rec])
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+1 record)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
