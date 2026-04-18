#!/usr/bin/env python3
"""Phase 0.5a feasibility proof — OLIR / OSCAL catalogue ingest end-to-end.

What this proves:
  * NIST publishes authoritative cybersecurity standards as public-domain JSON
    (OSCAL catalogues) on github.com/usnistgov/OSCAL-content.
  * Our ingest pipeline can parse them and produce the normalised control graph
    we need in ``data/crosswalks/`` for Phase 1.
  * SHA256 + HTTP headers give us reproducible provenance.

What this DOES NOT prove (by design — documented as Phase 1 risk):
  * The official CSF 2.0 ↔ 800-53 Rev.5 OLIR crosswalk is NOT shipped as a
    clean JSON asset. NIST released it in April 2024 as a draft XLSX for
    public comment. Until NIST publishes the final crosswalk in JSON, Phase 1
    will need to either
      (a) convert CPRT XLSX via openpyxl and emit our own normalised JSON, OR
      (b) sponsor the NIST sec-cert@nist.gov team to publish OLIR in CPRT JSON.
    Both are engineering, not research — no blocker to the gold-standard plan.

Run:
  .venv-feasibility/bin/python scripts/feasibility/olir_ingest_proof.py
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO / "data" / "crosswalks" / "olir"
VENDOR_DIR = REPO / "vendor" / "olir"

SOURCES = [
    {
        "id": "nist-csf-v2",
        "url": "https://raw.githubusercontent.com/usnistgov/OSCAL-content/main/nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json",
        "local": VENDOR_DIR / "nist_csf_v2_catalog.json",
        "kind": "oscal-catalog",
    },
    {
        "id": "nist-sp-800-53-r5",
        "url": "https://raw.githubusercontent.com/usnistgov/OSCAL-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
        "local": VENDOR_DIR / "nist_sp_800_53_r5_catalog.json",
        "kind": "oscal-catalog",
    },
]


def fetch(url: str, dest: pathlib.Path) -> dict:
    """Download ``url`` to ``dest`` unless cached; return provenance record."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with urllib.request.urlopen(url) as response:
            dest.write_bytes(response.read())
    payload = dest.read_bytes()
    return {
        "url": url,
        "local": str(dest.relative_to(REPO)),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def flatten_controls(group: dict, acc: list[dict], path: list[str]) -> None:
    """Walk OSCAL group/control tree and flatten controls with their breadcrumb."""
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
            }
        )
        if control.get("controls"):
            flatten_controls(control, acc, here + [control.get("id")])
    for sub in group.get("groups", []) or []:
        flatten_controls(sub, acc, here)


def normalise_oscal_catalog(source_id: str, catalog_json: dict) -> dict:
    cat = catalog_json["catalog"]
    metadata = cat.get("metadata", {})
    controls: list[dict] = []
    for group in cat.get("groups", []) or []:
        flatten_controls(group, controls, [])
    return {
        "source_id": source_id,
        "title": metadata.get("title"),
        "version": metadata.get("version"),
        "oscal_version": metadata.get("oscal-version"),
        "last_modified": metadata.get("last-modified"),
        "control_count": len(controls),
        "controls": controls,
    }


def run() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    provenance: list[dict] = []
    findings: list[str] = []

    for source in SOURCES:
        print(f"- fetching {source['id']} ...")
        prov = fetch(source["url"], source["local"])
        provenance.append({"source_id": source["id"], **prov})

        with source["local"].open("r", encoding="utf-8") as handle:
            catalog_json = json.load(handle)

        normalised = normalise_oscal_catalog(source["id"], catalog_json)
        out_path = OUTPUT_DIR / f"{source['id']}.normalised.json"
        with out_path.open("w", encoding="utf-8") as handle:
            json.dump(normalised, handle, indent=2)

        print(
            f"  ok: {normalised['title']} v{normalised['version']} "
            f"({normalised['control_count']} controls) -> {out_path.relative_to(REPO)}"
        )

        link_rels = {}
        for c in normalised["controls"]:
            for link in c["links"]:
                link_rels[link["rel"]] = link_rels.get(link["rel"], 0) + 1
        if link_rels:
            top = ", ".join(f"{rel}={n}" for rel, n in sorted(link_rels.items(), key=lambda x: -x[1])[:4])
            findings.append(f"{source['id']}: inline links present ({top})")
        else:
            findings.append(
                f"{source['id']}: no inline cross-framework links — relationships live in a separate OLIR/Profile artefact"
            )

    manifest_path = OUTPUT_DIR / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump({"provenance": provenance, "findings": findings}, handle, indent=2)

    print(f"\nmanifest: {manifest_path.relative_to(REPO)}")
    for finding in findings:
        print(f"  - {finding}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
