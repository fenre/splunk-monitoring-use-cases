"""Production ingest: NIST OSCAL catalogues and baseline profiles.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/ingest/ingest_oscal.py to src/splunk_uc/ingest/oscal.py.
parents[3] resolves: oscal.py -> ingest/ -> splunk_uc/ -> src/ -> repo
root. The legacy ``parents[2]`` chain assumed a depth of two (script
in scripts/ingest/, parents[2] reaches the repo root) and is now wrong
by one level. The legacy shim at scripts/ingest/ingest_oscal.py
re-exports ``main`` so any direct CLI invocation still works during
the soak period; the manifest helper sibling
(``scripts/ingest/manifest.py``) is also a shim so the legacy
``from manifest import ...`` import path still resolves.

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
  python -m splunk_uc ingest-oscal

Exits 0 on success, non-zero on any fetch / normalisation failure.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

from splunk_uc.ingest.manifest import FetchRecord, fetch, merge_into_manifest

_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[3]

MANIFEST_PATH = _REPO / "data" / "provenance" / "ingest-manifest.json"
VENDOR_DIR = _REPO / "vendor" / "oscal"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "oscal"

_OSCAL_BASE = "https://raw.githubusercontent.com/usnistgov/OSCAL-content/main/nist.gov"

SOURCES: list[dict[str, Any]] = [
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


def _flatten(group: dict[str, Any], acc: list[dict[str, Any]], path: list[str]) -> None:
    here = [*path, group.get("id") or group.get("title") or "?"]
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
            _flatten(control, acc, [*here, control.get("id")])
    for sub in group.get("groups", []) or []:
        _flatten(sub, acc, here)


def _normalise_catalog(source_id: str, doc: dict[str, Any]) -> dict[str, Any]:
    cat = doc["catalog"]
    meta = cat.get("metadata", {})
    controls: list[dict[str, Any]] = []
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


def _normalise_profile(source_id: str, doc: dict[str, Any]) -> dict[str, Any]:
    prof = doc["profile"]
    meta = prof.get("metadata", {})
    includes: list[dict[str, Any]] = []
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

    records: list[FetchRecord] = []
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
        print(
            f"  ok: {normalised['title']} v{normalised['version']} ({stat}) -> {out.relative_to(_REPO)}"
        )

    merge_into_manifest(MANIFEST_PATH, records)
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+{len(records)} records)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` is accepted for the registry contract but is unused: the OSCAL ingest takes no flags."""
    del argv
    return run()


if __name__ == "__main__":
    sys.exit(main())
