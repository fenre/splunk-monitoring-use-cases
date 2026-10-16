"""Write the fabric to parquet, the JSON API, and the facet index.

Parquet is written when pyarrow is installed. The JSON API and the facet
index use only the standard library, so a checkout can still serve
``/api/v1/fabric/`` without the build extra.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from splunk_uc.fabric import PREDICATES
from splunk_uc.fabric.resolve import Fabric

TYPE_SLUG = {
    "usecase": "usecase",
    "sourcetype": "sourcetype",
    "vendorProduct": "vendor-product",
    "addon": "addon",
    "cimDataset": "cim-dataset",
    "cimField": "cim-field",
    "complianceControl": "compliance-control",
    "industry": "industry",
    "businessOutcome": "business-outcome",
    "businessArea": "business-area",
    "persona": "persona",
}
SLUG_TYPE = {slug: name for name, slug in TYPE_SLUG.items()}

# Search tokens for the plan's Palo Alto example. These expand queries.
# They are not identity links: pan:traffic stays unlinked on emittedBy
# when the registry vote was split.
SEARCH_SYNONYMS: dict[str, tuple[str, ...]] = {
    "paloalto": ("pan", "palo alto"),
}

_FACET_DIMS = ("sourcetype", "vendorProduct", "addon", "cimDataset")
_DIM_TYPE = {
    "sourcetype": "sourcetype",
    "vendorProduct": "vendorProduct",
    "addon": "addon",
    "cimDataset": "cimDataset",
}


def _dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dumps(payload), encoding="utf-8")


def write_parquet(fabric: Fabric, out_dir: Path) -> bool:
    """Write ``entities.parquet`` and ``relationships.parquet``.

    Returns False when pyarrow is not installed. Rows are sorted and
    compression is off so two builds in one environment match byte for byte.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    entities = pa.table(
        {
            "id": [row["id"] for row in fabric.entities],
            "type": [row["type"] for row in fabric.entities],
            "label": [row["label"] for row in fabric.entities],
            "aliases": [json.dumps(row["aliases"], ensure_ascii=False) for row in fabric.entities],
        }
    )
    relationships = pa.table(
        {
            "source": [row[0] for row in fabric.relationships],
            "predicate": [row[1] for row in fabric.relationships],
            "target": [row[2] for row in fabric.relationships],
            "provenance": [row[3] for row in fabric.relationships],
            "confidence": [row[4] for row in fabric.relationships],
        }
    )
    opts = {"compression": "NONE", "use_dictionary": False, "write_statistics": True}
    pq.write_table(entities, out_dir / "entities.parquet", **opts)
    pq.write_table(relationships, out_dir / "relationships.parquet", **opts)
    return True


def _entity_lookup(fabric: Fabric) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["type"], row["id"]): row for row in fabric.entities}


def _adjacency(
    fabric: Fabric,
) -> tuple[
    dict[tuple[str, str], dict[str, list[dict[str, Any]]]],
    dict[tuple[str, str], dict[str, list[dict[str, Any]]]],
]:
    outgoing: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    incoming: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for source, predicate, target, provenance, confidence in fabric.relationships:
        source_type, target_type = PREDICATES[predicate]
        ref = {"id": target, "provenance": provenance, "confidence": confidence}
        outgoing[(source_type, source)][predicate].append(ref)
        incoming[(target_type, target)][predicate].append(
            {"id": source, "provenance": provenance, "confidence": confidence}
        )
    return outgoing, incoming


def write_api(fabric: Fabric, out_root: Path) -> None:
    """Write ``/api/v1/fabric/index.json`` and one document per entity."""
    lookup = _entity_lookup(fabric)
    outgoing, incoming = _adjacency(fabric)
    aliases: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_alias: set[tuple[str, str, str]] = set()
    for entity in fabric.entities:
        names = [entity["id"], entity["label"], *entity["aliases"]]
        for name in names:
            key = name.casefold()
            marker = (key, entity["type"], entity["id"])
            if not key or marker in seen_alias:
                continue
            seen_alias.add(marker)
            aliases[key].append(
                {"id": entity["id"], "label": entity["label"], "type": entity["type"]}
            )
    alias_payload = {
        key: sorted(value, key=lambda row: (row["type"], row["id"]))
        for key, value in sorted(aliases.items())
    }
    _write(
        out_root / "index.json",
        {
            "aliases": alias_payload,
            "entityCount": len(fabric.entities),
            "relationshipCount": len(fabric.relationships),
            "types": TYPE_SLUG,
        },
    )
    for entity in fabric.entities:
        key = (entity["type"], entity["id"])
        neighbors: dict[str, dict[str, list[dict[str, Any]]]] = {}
        predicates = set(outgoing.get(key, {})) | set(incoming.get(key, {}))
        for predicate in sorted(predicates):
            neighbors[predicate] = {
                "in": sorted(incoming.get(key, {}).get(predicate, []), key=lambda row: row["id"]),
                "out": sorted(outgoing.get(key, {}).get(predicate, []), key=lambda row: row["id"]),
            }
        slug = TYPE_SLUG[entity["type"]]
        _write(
            out_root / slug / f"{entity['id']}.json",
            {
                "aliases": entity["aliases"],
                "id": entity["id"],
                "label": entity["label"],
                "neighbors": neighbors,
                "type": entity["type"],
            },
        )
    _ = lookup


def facet_payload(fabric: Fabric, *, dropdown_limit: int = 40) -> dict[str, Any]:
    """Per-value counts and capped pairwise intersections."""
    lookup = _entity_lookup(fabric)
    counts: dict[str, Counter[str]] = {dim: Counter() for dim in _FACET_DIMS}
    for groups in fabric.members.values():
        for dim in _FACET_DIMS:
            counts[dim].update(groups.get(dim) or [])

    def label_for(dim: str, entity_id: str) -> str:
        entity = lookup.get((_DIM_TYPE[dim], entity_id))
        return entity["label"] if entity else entity_id

    values = {
        dim: [
            {"count": count, "id": entity_id, "label": label_for(dim, entity_id)}
            for entity_id, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        ]
        for dim, counter in counts.items()
    }
    top: dict[str, set[str]] = {}
    for dim, counter in counts.items():
        top[dim] = {
            entity_id
            for entity_id, count in counter.most_common(50)
            if count >= 5
        }
    pairs: Counter[tuple[str, str, str, str]] = Counter()
    for groups in fabric.members.values():
        for left_index, left in enumerate(_FACET_DIMS):
            left_ids = [entity_id for entity_id in groups.get(left) or [] if entity_id in top[left]]
            for right in _FACET_DIMS[left_index + 1 :]:
                right_ids = [
                    entity_id for entity_id in groups.get(right) or [] if entity_id in top[right]
                ]
                for left_id in left_ids:
                    for right_id in right_ids:
                        pairs[(left, left_id, right, right_id)] += 1
    intersections = [
        {
            "count": count,
            "left": left,
            "leftId": left_id,
            "right": right,
            "rightId": right_id,
        }
        for (left, left_id, right, right_id), count in pairs.items()
        if count >= 5
    ]
    intersections.sort(key=lambda row: (-row["count"], row["left"], row["leftId"], row["right"], row["rightId"]))
    dropdown = {
        dim: values[dim][:dropdown_limit]
        for dim in _FACET_DIMS
    }
    return {
        "dropdown": dropdown,
        "intersections": intersections[:2000],
        "values": values,
    }


def write_facets(fabric: Fabric, path: Path) -> dict[str, Any]:
    payload = facet_payload(fabric)
    _write(path, payload)
    return payload


def alias_text(fabric: Fabric) -> dict[str, str]:
    """Extra search text per use case, from linked entity names and synonyms."""
    lookup = _entity_lookup(fabric)
    out: dict[str, str] = {}
    type_for = _DIM_TYPE
    for uc_id, groups in fabric.members.items():
        parts: list[str] = []
        for dim, entity_ids in groups.items():
            entity_type = type_for[dim]
            for entity_id in entity_ids:
                entity = lookup.get((entity_type, entity_id))
                if entity is None:
                    continue
                parts.append(entity["id"])
                parts.append(entity["label"])
                parts.extend(entity["aliases"])
                for synonym in SEARCH_SYNONYMS.get(entity_id, ()):
                    parts.append(synonym)
        if parts:
            out[uc_id] = " ".join(parts)
    return out


def attach_catalog(catalog: Any, fabric: Fabric) -> None:
    """Copy fabric ids and alias text onto in-memory catalogue use cases.

    ``fs`` / ``fv`` / ``fa`` / ``fc`` drive the facet filters. ``fx`` is
    indexed by the search stage so alias spellings hit the same use cases.
    """
    texts = alias_text(fabric)
    for _cat, _sub, uc in catalog.iter_ucs():
        uc_id = uc.get("i")
        if not uc_id:
            continue
        groups = fabric.members.get(str(uc_id), {})
        uc["fs"] = list(groups.get("sourcetype") or [])
        uc["fv"] = list(groups.get("vendorProduct") or [])
        uc["fa"] = list(groups.get("addon") or [])
        uc["fc"] = list(groups.get("cimDataset") or [])
        extra = texts.get(str(uc_id))
        if extra:
            uc["fx"] = extra
    payload = facet_payload(fabric)
    catalog.facets["fabric"] = payload["dropdown"]
    catalog._fabric = fabric
