"""Production ingest: MITRE D3FEND ontology + ATT&CK mapping.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/ingest/ingest_d3fend.py to src/splunk_uc/ingest/d3fend.py.
parents[3] resolves: d3fend.py -> ingest/ -> splunk_uc/ -> src/ ->
repo root. The legacy ``parents[2]`` chain assumed depth two and is
now wrong by one level. The legacy shim at
scripts/ingest/ingest_d3fend.py re-exports ``main`` and ``run`` so
the orchestrator (``scripts/ingest_all.py``) and any direct CLI
invocation still work unchanged during the soak period.

Sources:
  * D3FEND full JSON-LD ontology: https://d3fend.mitre.org/ontologies/d3fend.json
  * D3FEND inferred relationships: https://d3fend.mitre.org/api/ontology/inference/d3fend-full-mappings.json

The driver:
  1. Downloads both artefacts to ``vendor/d3fend/``.
  2. Records SHA-256 + HTTP metadata in the shared manifest.
  3. Emits a flat normalised view under ``data/crosswalks/d3fend/`` with:
       * ``d3fend-techniques.normalised.json`` -- every
         ``d3f:DefensiveTechnique`` node with label, definition, parent,
         and linked references.
       * ``d3fend-attack-mappings.normalised.json`` -- pairs
         ``{attack_id -> [d3fend_technique_id, ...]}`` derived from the
         inferred relationships bundle.

Run:
  python -m splunk_uc ingest-d3fend
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

from splunk_uc.ingest.manifest import FetchRecord, fetch, merge_into_manifest

_HERE = pathlib.Path(__file__).resolve()
_REPO = _HERE.parents[3]

MANIFEST_PATH = _REPO / "data" / "provenance" / "ingest-manifest.json"
VENDOR_DIR = _REPO / "vendor" / "d3fend"
CROSSWALK_DIR = _REPO / "data" / "crosswalks" / "d3fend"

SOURCES: list[dict[str, Any]] = [
    {
        "id": "d3fend-ontology",
        "url": "https://d3fend.mitre.org/ontologies/d3fend.json",
        "local": VENDOR_DIR / "d3fend.json",
    },
    {
        "id": "d3fend-full-mappings",
        "url": "https://d3fend.mitre.org/api/ontology/inference/d3fend-full-mappings.json",
        "local": VENDOR_DIR / "d3fend-full-mappings.json",
    },
]

_ATTACK_ID_RE = re.compile(r"T\d{4}(?:\.\d{3})?")


def _str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        result = value.get("@value") or value.get("@id")
        return str(result) if result is not None else None
    if isinstance(value, list):
        for item in value:
            s = _str(item)
            if s:
                return s
    return None


def _list_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            s = _str(item)
            if s:
                out.append(s)
        return out
    s = _str(value)
    return [s] if s else []


def _short_id(iri: str) -> str:
    if not iri:
        return ""
    if "#" in iri:
        return iri.split("#", 1)[1]
    return iri.rsplit("/", 1)[-1]


def _normalise_ontology(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract every ``d3f:DefensiveTechnique`` descendant from the ontology.

    D3FEND models defensive techniques as an OWL class hierarchy, not as
    top-level instances. We therefore walk ``rdfs:subClassOf`` transitively
    and keep every ``owl:Class`` whose ancestor set contains
    ``d3f:DefensiveTechnique``.
    """

    graph = doc.get("@graph") or []
    by_id: dict[str, dict[str, Any]] = {}
    parents: dict[str, list[str]] = {}
    for node in graph:
        nid = _str(node.get("@id"))
        if not nid:
            continue
        by_id[nid] = node
        raw_parents = node.get("rdfs:subClassOf") or []
        if isinstance(raw_parents, dict):
            raw_parents = [raw_parents]
        if isinstance(raw_parents, str):
            raw_parents = [{"@id": raw_parents}]
        pids: list[str] = []
        for p in raw_parents:
            if isinstance(p, dict):
                pid = _str(p.get("@id"))
                if pid:
                    pids.append(pid)
        parents[nid] = pids

    def _ancestors(cid: str) -> set[str]:
        seen: set[str] = set()
        stack = list(parents.get(cid, []))
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            stack.extend(parents.get(p, []))
        return seen

    target = "d3f:DefensiveTechnique"
    techniques: list[dict[str, Any]] = []

    for nid, node in by_id.items():
        types = _list_str(node.get("@type"))
        if "owl:Class" not in types:
            continue
        anc = _ancestors(nid)
        if target not in anc and nid != target:
            continue

        iri = nid
        techniques.append(
            {
                "iri": iri,
                "id": _short_id(iri),
                "label": _str(node.get("rdfs:label")),
                "definition": _str(
                    node.get("http://www.w3.org/2000/01/rdf-schema#comment")
                    or node.get("rdfs:comment")
                    or node.get("d3f:definition")
                    or node.get("d3f:d3fend-full-definition")
                ),
                "parents": parents.get(nid, []),
                "is_terminal": not any(
                    target in _ancestors(other) and nid in parents.get(other, []) for other in by_id
                ),
            }
        )

    techniques.sort(key=lambda t: (t["id"] or "", t["iri"]))

    return {
        "source": "d3fend-ontology",
        "techniques_count": len(techniques),
        "techniques": techniques,
    }


def _normalise_mappings(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract (d3fend-technique, offensive-attack-id) pairs."""

    mappings: dict[str, list[str]] = {}

    def _scan(value: Any) -> None:
        if isinstance(value, dict):
            for v in value.values():
                _scan(v)
        elif isinstance(value, list):
            for v in value:
                _scan(v)
        elif isinstance(value, str):
            for hit in _ATTACK_ID_RE.findall(value):
                mappings.setdefault(hit, [])

    def _scan_bindings() -> None:
        """The inferred-mappings document uses SPARQL-results JSON shape."""

        results = (doc.get("results") or {}).get("bindings") or []
        for row in results:
            d3f_iri = ((row.get("def_tech") or {}).get("value")) or (
                (row.get("defensive_technique") or {}).get("value")
            )
            attack_id = (
                ((row.get("off_tech_id") or {}).get("value"))
                or ((row.get("offensive_technique_id") or {}).get("value"))
                or ((row.get("attack_id") or {}).get("value"))
            )
            if d3f_iri and attack_id:
                mappings.setdefault(attack_id.strip(), []).append(_short_id(d3f_iri))

    if "results" in doc and "bindings" in (doc.get("results") or {}):
        _scan_bindings()
    else:
        _scan(doc)

    for aid, ids in mappings.items():
        seen: set[str] = set()
        deduped: list[str] = []
        for i in ids:
            if i and i not in seen:
                seen.add(i)
                deduped.append(i)
        mappings[aid] = deduped

    return {
        "source": "d3fend-full-mappings",
        "attack_id_count": len(mappings),
        "mapping_pair_count": sum(len(v) for v in mappings.values()),
        "mappings": mappings,
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
        except Exception as err:
            print(f"  FAIL: {err}", file=sys.stderr)
            return 2
        records.append(rec)

    onto_doc = json.loads(SOURCES[0]["local"].read_text(encoding="utf-8"))
    mappings_doc = json.loads(SOURCES[1]["local"].read_text(encoding="utf-8"))

    onto_norm = _normalise_ontology(onto_doc)
    mapping_norm = _normalise_mappings(mappings_doc)

    (CROSSWALK_DIR / "d3fend-techniques.normalised.json").write_text(
        json.dumps(onto_norm, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (CROSSWALK_DIR / "d3fend-attack-mappings.normalised.json").write_text(
        json.dumps(mapping_norm, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(
        "  ok:",
        f"defensive_techniques={onto_norm['techniques_count']}",
        f"attack_ids_mapped={mapping_norm['attack_id_count']}",
        f"mapping_pairs={mapping_norm['mapping_pair_count']}",
    )

    merge_into_manifest(MANIFEST_PATH, records)
    print(f"\nManifest updated: {MANIFEST_PATH.relative_to(_REPO)} (+{len(records)} records)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` accepted for the registry contract; the D3FEND ingest takes no flags."""
    del argv
    return run()


if __name__ == "__main__":
    sys.exit(main())
