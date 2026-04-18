#!/usr/bin/env python3
"""Production ingest: cross-framework OLIR-style mappings.

Primary source:
    Center for Threat-Informed Defense (CTID) "Mappings Explorer"
    https://github.com/center-for-threat-informed-defense/mappings-explorer

The NIST Online Informative References (OLIR) programme curates
cross-framework crosswalks (e.g. NIST SP 800-53 rev5 ↔ ATT&CK,
CRI Profile ↔ ATT&CK, CSA CCM ↔ ATT&CK). While authoritative NIST
OLIR submissions live behind the OLIR web UI as per-mapping XLSX/CSV,
CTID's Mappings Explorer republishes the same data model in stable,
machine-readable JSON under a Creative Commons licence. We ingest
those JSON artefacts, record cryptographic provenance, and normalise
them into flat, catalogue-joinable crosswalks.

Outputs land under ``data/crosswalks/olir/`` and are keyed by the
pair (<framework>, <version>, <attack_version>) so new NIST / CTID
releases can be ingested side-by-side.

Run:
  .venv-feasibility/bin/python scripts/ingest/ingest_olir.py
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List

_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from manifest import FetchRecord, fetch, merge_into_manifest  # noqa: E402

MANIFEST_PATH = _REPO / "data" / "provenance" / "ingest-manifest.json"
VENDOR_DIR = _REPO / "vendor" / "olir"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "olir"

_CTID_BASE = "https://raw.githubusercontent.com/center-for-threat-informed-defense/mappings-explorer/main/mappings"

SOURCES: List[Dict] = [
    {
        "id": "ctid-nist-800-53-rev5-attack-16.1",
        "framework": "NIST SP 800-53 rev5",
        "framework_id": "nist-sp-800-53-r5",
        "framework_version": "rev5",
        "attack_version": "16.1",
        "attack_domain": "enterprise",
        "url": (
            f"{_CTID_BASE}/nist_800_53/attack-16.1/nist_800_53-rev5/enterprise/"
            "nist_800_53-rev5_attack-16.1-enterprise.json"
        ),
        "local": VENDOR_DIR / "nist-800-53-rev5_attack-16.1-enterprise.json",
    },
    {
        "id": "ctid-cri-profile-v2.1-attack-16.1",
        "framework": "CRI Profile",
        "framework_id": "cri-profile",
        "framework_version": "v2.1",
        "attack_version": "16.1",
        "attack_domain": "enterprise",
        "url": (
            f"{_CTID_BASE}/cri_profile/attack-16.1/cri_profile-v2.1/enterprise/"
            "cri_profile-v2.1_attack-16.1-enterprise.json"
        ),
        "local": VENDOR_DIR / "cri-profile-v2.1_attack-16.1-enterprise.json",
    },
    {
        "id": "ctid-csa-ccm-4.1-attack-17.1",
        "framework": "CSA Cloud Controls Matrix",
        "framework_id": "csa-ccm",
        "framework_version": "v4.1",
        "attack_version": "17.1",
        "attack_domain": "enterprise",
        "url": (
            f"{_CTID_BASE}/csa_ccm/attack-17.1/csa_ccm-4.1/enterprise/"
            "csa_ccm-4.1_attack-17.1-enterprise.json"
        ),
        "local": VENDOR_DIR / "csa-ccm-4.1_attack-17.1-enterprise.json",
    },
]


def _normalise(src: Dict, payload: Dict) -> Dict:
    """Normalise a CTID Mappings Explorer JSON file.

    The CTID schema is::

        {"metadata": {...}, "mapping_objects": [{"capability_id": ..., ...}]}

    We emit one record per mapping_object with provenance keys added so
    downstream joiners do not have to re-read the manifest.
    """

    objects = payload.get("mapping_objects") or []
    records: List[Dict] = []
    capability_idx: Dict[str, Dict] = {}
    attack_idx: Dict[str, Dict] = {}

    for obj in objects:
        capability_id = obj.get("capability_id")
        attack_id = obj.get("attack_object_id")
        mapping_type = obj.get("mapping_type") or ""
        status = obj.get("status") or ""
        if not capability_id or not attack_id:
            continue
        row = {
            "framework_id": src["framework_id"],
            "framework_version": src["framework_version"],
            "capability_id": capability_id,
            "capability_description": obj.get("capability_description"),
            "capability_group": obj.get("capability_group"),
            "attack_version": src["attack_version"],
            "attack_domain": src["attack_domain"],
            "attack_object_id": attack_id,
            "attack_object_name": obj.get("attack_object_name"),
            "mapping_type": mapping_type,
            "status": status,
            "comments": obj.get("comments"),
            "references": obj.get("references", []) or [],
        }
        records.append(row)
        capability_idx.setdefault(capability_id, {
            "capability_id": capability_id,
            "capability_group": obj.get("capability_group"),
            "description": obj.get("capability_description"),
            "attack_ids": [],
        })["attack_ids"].append(attack_id)
        attack_idx.setdefault(attack_id, {
            "attack_object_id": attack_id,
            "attack_object_name": obj.get("attack_object_name"),
            "capabilities": [],
        })["capabilities"].append(capability_id)

    for entry in capability_idx.values():
        entry["attack_ids"] = sorted(set(entry["attack_ids"]))
    for entry in attack_idx.values():
        entry["capabilities"] = sorted(set(entry["capabilities"]))

    records.sort(key=lambda r: (r["capability_id"], r["attack_object_id"]))

    return {
        "source": src["id"],
        "framework": src["framework"],
        "framework_id": src["framework_id"],
        "framework_version": src["framework_version"],
        "attack_version": src["attack_version"],
        "attack_domain": src["attack_domain"],
        "upstream_metadata": payload.get("metadata") or {},
        "mapping_count": len(records),
        "capabilities_mapped": len(capability_idx),
        "attack_ids_mapped": len(attack_idx),
        "mappings": records,
        "by_capability": sorted(capability_idx.values(), key=lambda r: r["capability_id"]),
        "by_attack": sorted(attack_idx.values(), key=lambda r: r["attack_object_id"]),
    }


def run() -> int:
    CROSSWALK_DIR.mkdir(parents=True, exist_ok=True)
    records: List[FetchRecord] = []
    summary: List[Dict] = []

    for src in SOURCES:
        print(f"- fetching {src['id']} ...", flush=True)
        try:
            rec = fetch(
                source_id=src["id"],
                url=src["url"],
                dest=src["local"],
                repo_root=_REPO,
            )
        except Exception as err:
            print(f"  FAIL: {err}", file=sys.stderr)
            return 2
        records.append(rec)

        with src["local"].open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        normalised = _normalise(src, payload)
        out = CROSSWALK_DIR / f"{src['id']}.normalised.json"
        out.write_text(
            json.dumps(normalised, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summary.append(
            {
                "source": src["id"],
                "mappings": normalised["mapping_count"],
                "capabilities": normalised["capabilities_mapped"],
                "attack_ids": normalised["attack_ids_mapped"],
            }
        )
        print(
            "  ok:",
            f"mappings={normalised['mapping_count']}",
            f"capabilities={normalised['capabilities_mapped']}",
            f"attack_ids={normalised['attack_ids_mapped']}",
        )

    index = {
        "source": "ctid-mappings-explorer",
        "sources": summary,
    }
    (CROSSWALK_DIR / "_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    merge_into_manifest(MANIFEST_PATH, records)
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+{len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
