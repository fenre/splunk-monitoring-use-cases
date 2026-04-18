#!/usr/bin/env python3
"""Production ingest: MITRE ATT&CK Enterprise STIX bundle.

Source: https://github.com/mitre/cti  (authoritative STIX 2.1 CTI)

The driver:
  1. Downloads the pinned-ref ATT&CK Enterprise bundle to
     ``vendor/attack/enterprise-attack.json``.
  2. Records SHA-256 + HTTP metadata in the shared manifest.
  3. Normalises techniques, sub-techniques, tactics, groups, software,
     mitigations, campaigns, and relationships into separate flat JSON
     files under ``data/crosswalks/attack/`` so downstream consumers can
     index by ATT&CK ID (e.g. ``T1059.001``) without re-parsing STIX.

Run:
  .venv-feasibility/bin/python scripts/ingest/ingest_attack.py

Exits 0 on success, non-zero on any fetch / normalisation failure.
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
VENDOR_DIR = _REPO / "vendor" / "attack"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "attack"

SOURCES: List[Dict] = [
    {
        "id": "mitre-attack-enterprise",
        "url": "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json",
        "local": VENDOR_DIR / "enterprise-attack.json",
        "domain": "enterprise",
    },
    {
        "id": "mitre-attack-ics",
        "url": "https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json",
        "local": VENDOR_DIR / "ics-attack.json",
        "domain": "ics",
    },
    {
        "id": "mitre-attack-mobile",
        "url": "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json",
        "local": VENDOR_DIR / "mobile-attack.json",
        "domain": "mobile",
    },
]


def _attack_id(obj: Dict) -> str:
    for ref in obj.get("external_references", []) or []:
        if ref.get("source_name", "").startswith("mitre-attack"):
            if ref.get("external_id"):
                return ref["external_id"]
    return ""


def _external_url(obj: Dict) -> str:
    for ref in obj.get("external_references", []) or []:
        if ref.get("source_name", "").startswith("mitre-attack") and ref.get("url"):
            return ref["url"]
    return ""


def _normalise(domain: str, bundle: Dict) -> Dict:
    techniques: List[Dict] = []
    tactics: List[Dict] = []
    mitigations: List[Dict] = []
    groups: List[Dict] = []
    software: List[Dict] = []
    campaigns: List[Dict] = []
    data_sources: List[Dict] = []
    data_components: List[Dict] = []
    relationships: List[Dict] = []

    for obj in bundle.get("objects", []) or []:
        typ = obj.get("type")
        revoked = bool(obj.get("revoked", False))
        deprecated = bool(obj.get("x_mitre_deprecated", False))
        base = {
            "stix_id": obj.get("id"),
            "name": obj.get("name"),
            "description": obj.get("description"),
            "attack_id": _attack_id(obj),
            "url": _external_url(obj),
            "revoked": revoked,
            "deprecated": deprecated,
            "created": obj.get("created"),
            "modified": obj.get("modified"),
        }
        if typ == "attack-pattern":
            phases = [p.get("phase_name") for p in obj.get("kill_chain_phases", []) or []]
            techniques.append(
                {
                    **base,
                    "tactics": phases,
                    "platforms": obj.get("x_mitre_platforms", []) or [],
                    "data_sources": obj.get("x_mitre_data_sources", []) or [],
                    "detection": obj.get("x_mitre_detection"),
                    "is_subtechnique": bool(obj.get("x_mitre_is_subtechnique", False)),
                }
            )
        elif typ == "x-mitre-tactic":
            tactics.append({**base, "shortname": obj.get("x_mitre_shortname")})
        elif typ == "course-of-action":
            mitigations.append(base)
        elif typ == "intrusion-set":
            groups.append({**base, "aliases": obj.get("aliases", []) or []})
        elif typ in ("malware", "tool"):
            software.append({**base, "software_type": typ})
        elif typ == "campaign":
            campaigns.append({**base, "aliases": obj.get("aliases", []) or []})
        elif typ == "x-mitre-data-source":
            data_sources.append(base)
        elif typ == "x-mitre-data-component":
            data_components.append(
                {**base, "data_source_ref": obj.get("x_mitre_data_source_ref")}
            )
        elif typ == "relationship":
            relationships.append(
                {
                    "stix_id": obj.get("id"),
                    "relationship_type": obj.get("relationship_type"),
                    "source_ref": obj.get("source_ref"),
                    "target_ref": obj.get("target_ref"),
                    "description": obj.get("description"),
                }
            )

    return {
        "domain": domain,
        "bundle_id": bundle.get("id"),
        "techniques_count": len(techniques),
        "tactics_count": len(tactics),
        "mitigations_count": len(mitigations),
        "groups_count": len(groups),
        "software_count": len(software),
        "campaigns_count": len(campaigns),
        "data_sources_count": len(data_sources),
        "data_components_count": len(data_components),
        "relationships_count": len(relationships),
        "techniques": techniques,
        "tactics": tactics,
        "mitigations": mitigations,
        "groups": groups,
        "software": software,
        "campaigns": campaigns,
        "data_sources": data_sources,
        "data_components": data_components,
        "relationships": relationships,
    }


def run() -> int:
    CROSSWALK_DIR.mkdir(parents=True, exist_ok=True)
    records: List[FetchRecord] = []
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
            bundle = json.load(handle)

        normalised = _normalise(src["domain"], bundle)
        out = CROSSWALK_DIR / f"{src['id']}.normalised.json"
        out.write_text(
            json.dumps(normalised, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            "  ok:",
            f"techniques={normalised['techniques_count']}",
            f"tactics={normalised['tactics_count']}",
            f"mitigations={normalised['mitigations_count']}",
            f"groups={normalised['groups_count']}",
            f"software={normalised['software_count']}",
            f"campaigns={normalised['campaigns_count']}",
            "->",
            out.relative_to(_REPO),
        )

    merge_into_manifest(MANIFEST_PATH, records)
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+{len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
