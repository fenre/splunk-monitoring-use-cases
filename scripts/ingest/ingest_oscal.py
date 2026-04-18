#!/usr/bin/env python3
"""Production ingest: NIST OSCAL catalogues and baseline profiles.

Sources (all from the ``usnistgov/OSCAL-content`` mirror maintained by
the NIST OSCAL team):

  * NIST Cybersecurity Framework 2.0 catalogue
  * NIST SP 800-53 rev.5 catalogue
  * NIST SP 800-53 rev.5 LOW / MODERATE / HIGH baseline profiles
  * NIST SP 800-171 rev.3 catalogue

The driver:
  1. Downloads each asset to ``vendor/oscal/`` (cached if already present).
  2. Records SHA-256 + HTTP metadata in
     ``data/provenance/ingest-manifest.json``.
  3. Normalises the OSCAL control tree into a flat list under
     ``data/crosswalks/oscal/<source_id>.normalised.json``.

Run:
  .venv-feasibility/bin/python scripts/ingest/ingest_oscal.py

Exits 0 on success, non-zero on any fetch / normalisation failure.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List

# Allow running as a script ('python scripts/ingest/ingest_oscal.py')
_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from manifest import FetchRecord, fetch, merge_into_manifest  # noqa: E402

MANIFEST_PATH = _REPO / "data" / "provenance" / "ingest-manifest.json"
VENDOR_DIR = _REPO / "vendor" / "oscal"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "oscal"

_OSCAL_BASE = "https://raw.githubusercontent.com/usnistgov/OSCAL-content/main/nist.gov"

SOURCES: List[Dict] = [
    {
        "id": "nist-csf-v2",
        "url": f"{_OSCAL_BASE}/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json",
        "local": VENDOR_DIR / "nist_csf_v2_catalog.json",
        "kind": "catalog",
    },
    {
        "id": "nist-sp-800-53-r5",
        "url": f"{_OSCAL_BASE}/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
        "local": VENDOR_DIR / "nist_sp_800_53_r5_catalog.json",
        "kind": "catalog",
    },
    {
        "id": "nist-sp-800-53-r5-low",
        "url": f"{_OSCAL_BASE}/SP800-53/rev5/json/NIST_SP-800-53_rev5_LOW-baseline_profile.json",
        "local": VENDOR_DIR / "nist_sp_800_53_r5_LOW_profile.json",
        "kind": "profile",
    },
    {
        "id": "nist-sp-800-53-r5-moderate",
        "url": f"{_OSCAL_BASE}/SP800-53/rev5/json/NIST_SP-800-53_rev5_MODERATE-baseline_profile.json",
        "local": VENDOR_DIR / "nist_sp_800_53_r5_MODERATE_profile.json",
        "kind": "profile",
    },
    {
        "id": "nist-sp-800-53-r5-high",
        "url": f"{_OSCAL_BASE}/SP800-53/rev5/json/NIST_SP-800-53_rev5_HIGH-baseline_profile.json",
        "local": VENDOR_DIR / "nist_sp_800_53_r5_HIGH_profile.json",
        "kind": "profile",
    },
    {
        "id": "nist-sp-800-171-r3",
        "url": f"{_OSCAL_BASE}/SP800-171/rev3/json/NIST_SP800-171_rev3_catalog.json",
        "local": VENDOR_DIR / "nist_sp_800_171_r3_catalog.json",
        "kind": "catalog",
    },
    {
        "id": "nist-sp-800-218-ssdf",
        "url": f"{_OSCAL_BASE}/SP800-218/ver1/json/NIST_SP800-218_ver1_catalog.json",
        "local": VENDOR_DIR / "nist_sp_800_218_ssdf_catalog.json",
        "kind": "catalog",
    },
]


def _flatten(group: Dict, acc: List[Dict], path: List[str]) -> None:
    here = path + [group.get("id") or group.get("title") or "?"]
    for control in group.get("controls", []) or []:
        acc.append(
            {
                "id": control.get("id"),
                "title": control.get("title"),
                "path": " / ".join(here),
                "has_children": bool(control.get("controls")),
                "links": [
                    {"rel": link.get("rel"), "href": link.get("href")}
                    for link in control.get("links", []) or []
                ],
                "props": [
                    {"name": p.get("name"), "value": p.get("value"), "ns": p.get("ns")}
                    for p in control.get("props", []) or []
                    if p.get("name")
                ],
            }
        )
        if control.get("controls"):
            _flatten(control, acc, here + [control.get("id")])
    for sub in group.get("groups", []) or []:
        _flatten(sub, acc, here)


def _normalise_catalog(source_id: str, doc: Dict) -> Dict:
    cat = doc["catalog"]
    meta = cat.get("metadata", {})
    controls: List[Dict] = []
    for group in cat.get("groups", []) or []:
        _flatten(group, controls, [])
    return {
        "source_id": source_id,
        "kind": "catalog",
        "title": meta.get("title"),
        "version": meta.get("version"),
        "oscal_version": meta.get("oscal-version"),
        "last_modified": meta.get("last-modified"),
        "control_count": len(controls),
        "controls": controls,
    }


def _normalise_profile(source_id: str, doc: Dict) -> Dict:
    prof = doc["profile"]
    meta = prof.get("metadata", {})
    includes: List[Dict] = []
    for imp in prof.get("imports", []) or []:
        for inc in imp.get("include-controls", []) or []:
            for wid in inc.get("with-ids", []) or []:
                includes.append({"import": imp.get("href"), "control_id": wid})
    return {
        "source_id": source_id,
        "kind": "profile",
        "title": meta.get("title"),
        "version": meta.get("version"),
        "oscal_version": meta.get("oscal-version"),
        "last_modified": meta.get("last-modified"),
        "included_control_count": len(includes),
        "included_controls": includes,
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
        except Exception as err:  # pragma: no cover - network failure path
            print(f"  FAIL: {err}", file=sys.stderr)
            return 2
        records.append(rec)

        with src["local"].open("r", encoding="utf-8") as handle:
            doc = json.load(handle)

        if src["kind"] == "catalog":
            normalised = _normalise_catalog(src["id"], doc)
            stat = f"{normalised['control_count']} controls"
        elif src["kind"] == "profile":
            normalised = _normalise_profile(src["id"], doc)
            stat = f"{normalised['included_control_count']} included controls"
        else:
            print(f"  FAIL: unknown kind {src['kind']!r}", file=sys.stderr)
            return 2

        out = CROSSWALK_DIR / f"{src['id']}.normalised.json"
        out.write_text(
            json.dumps(normalised, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"  ok: {normalised['title']} v{normalised['version']} ({stat}) -> {out.relative_to(_REPO)}")

    merge_into_manifest(MANIFEST_PATH, records)
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+{len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(run())
