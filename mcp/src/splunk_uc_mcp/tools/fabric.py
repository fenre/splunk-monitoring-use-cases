"""Fabric tools: ``get_entity``, ``get_neighbors``, ``find_related_use_cases``.

These read ``api/v1/fabric/``. An alias such as ``pan:traffic`` or
``Splunk_TA_paloalto`` resolves to the canonical entity. When several
entities share an alias, the tool lists them and does not pick one.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError

_TYPE_SLUG = {
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
_SLUG_TYPE = {slug: name for name, slug in _TYPE_SLUG.items()}

GET_ENTITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entity_id"],
    "properties": {
        "entity_id": {
            "type": "string",
            "description": "Canonical id or an alias (pan:traffic, Splunk_TA_paloalto, UC-5.1.1).",
            "minLength": 1,
            "maxLength": 200,
        },
        "entity_type": {
            "type": "string",
            "description": "Optional entity type (sourcetype, vendorProduct, or the URL slug vendor-product) when an alias is shared.",
        },
    },
    "additionalProperties": False,
}

GET_ENTITY_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "type", "label"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string"},
        "label": {"type": "string"},
        "aliases": {"type": "array", "items": {"type": "string"}},
        "neighbors": {"type": "object"},
        "ambiguous": {"type": "boolean"},
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "label"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                    "label": {"type": "string"},
                },
            },
        },
    },
}

GET_NEIGHBORS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entity_id"],
    "properties": {
        "entity_id": {"type": "string", "minLength": 1, "maxLength": 200},
        "entity_type": {"type": "string"},
        "predicate": {"type": "string"},
        "direction": {"type": "string", "enum": ["in", "out"]},
    },
    "additionalProperties": False,
}

GET_NEIGHBORS_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "type", "neighbors"],
    "properties": {
        "id": {"type": "string"},
        "type": {"type": "string"},
        "neighbors": {"type": "object"},
    },
}

FIND_RELATED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entity_id"],
    "properties": {
        "entity_id": {"type": "string", "minLength": 1, "maxLength": 200},
        "entity_type": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
    },
    "additionalProperties": False,
}

FIND_RELATED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entity", "count", "useCases"],
    "properties": {
        "entity": {
            "type": "object",
            "required": ["id", "type", "label"],
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "label": {"type": "string"},
            },
        },
        "count": {"type": "integer", "minimum": 0},
        "useCases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "score"],
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer"},
                    "label": {"type": "string"},
                },
            },
        },
    },
}


def _check_id(entity_id: str) -> str:
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValueError("entity_id is required")
    if len(entity_id) > 200 or any(char in entity_id for char in "/\\") or ".." in entity_id:
        raise ValueError(f"entity_id is not a fabric id or alias: {entity_id!r}")
    return entity_id.strip()


def _index(catalog: Catalog) -> dict[str, Any]:
    cached = getattr(catalog, "_fabric_index", None)
    if cached is None:
        cached = catalog.load_json("fabric", "index.json")
        catalog._fabric_index = cached
    return cached


def _matches(catalog: Catalog, entity_id: str, entity_type: str | None) -> list[dict[str, str]]:
    index = _index(catalog)
    found = list(index.get("aliases", {}).get(entity_id.casefold(), []))
    if entity_type:
        wanted = _SLUG_TYPE.get(entity_type, entity_type)
        found = [row for row in found if row["type"] == wanted]
    return found


def _load_match(catalog: Catalog, match: dict[str, str]) -> dict[str, Any]:
    slug = _TYPE_SLUG[match["type"]]
    return catalog.load_json("fabric", slug, f"{match['id']}.json")


def get_entity(
    *,
    catalog: Catalog,
    entity_id: str,
    entity_type: str | None = None,
) -> dict[str, Any]:
    """Return one entity, or the list of matches when an alias is shared."""
    entity_id = _check_id(entity_id)
    found = _matches(catalog, entity_id, entity_type)
    if not found:
        raise CatalogNotFoundError(f"No fabric entity matches {entity_id!r}")
    if len(found) > 1:
        return {"ambiguous": True, "id": entity_id, "type": entity_type or "", "label": entity_id, "matches": found}
    return _load_match(catalog, found[0])


def _neighbor_ids(doc: dict[str, Any], predicate: str, direction: str) -> list[str]:
    block = doc.get("neighbors", {}).get(predicate, {})
    return [row["id"] for row in block.get(direction, [])]


def get_neighbors(
    *,
    catalog: Catalog,
    entity_id: str,
    entity_type: str | None = None,
    predicate: str | None = None,
    direction: str | None = None,
) -> dict[str, Any]:
    """Neighbours of one entity, optionally one predicate and direction."""
    doc = get_entity(catalog=catalog, entity_id=entity_id, entity_type=entity_type)
    if doc.get("ambiguous"):
        raise ValueError("alias matches more than one entity; pass entity_type")
    neighbors = doc.get("neighbors") or {}
    if predicate:
        neighbors = {predicate: neighbors.get(predicate, {"in": [], "out": []})}
    if direction:
        neighbors = {
            name: {direction: block.get(direction, [])}
            for name, block in neighbors.items()
        }
    return {"id": doc["id"], "type": doc["type"], "neighbors": neighbors}


def _related_ids(catalog: Catalog, doc: dict[str, Any]) -> Counter[str]:
    """Score use cases by shared sourcetypes (3) and vendor products (2)."""
    scores: Counter[str] = Counter()
    kind = doc["type"]
    if kind == "usecase":
        for sourcetype_id in _neighbor_ids(doc, "uses", "out"):
            other = _load_match(catalog, {"type": "sourcetype", "id": sourcetype_id, "label": ""})
            for uc_id in _neighbor_ids(other, "uses", "in"):
                if uc_id != doc["id"]:
                    scores[uc_id] += 3
        for vendor_id in _neighbor_ids(doc, "runsOn", "out"):
            other = _load_match(catalog, {"type": "vendorProduct", "id": vendor_id, "label": ""})
            for uc_id in _neighbor_ids(other, "runsOn", "in"):
                if uc_id != doc["id"]:
                    scores[uc_id] += 2
        return scores
    if kind == "sourcetype":
        for uc_id in _neighbor_ids(doc, "uses", "in"):
            scores[uc_id] += 3
        for vendor_id in _neighbor_ids(doc, "emittedBy", "out"):
            other = _load_match(catalog, {"type": "vendorProduct", "id": vendor_id, "label": ""})
            users = set(_neighbor_ids(other, "runsOn", "in"))
            for uc_id in list(scores):
                if uc_id in users:
                    scores[uc_id] += 2
        return scores
    if kind == "vendorProduct":
        for uc_id in _neighbor_ids(doc, "runsOn", "in"):
            scores[uc_id] += 2
        return scores
    if kind == "addon":
        for sourcetype_id in _neighbor_ids(doc, "producedBy", "in"):
            other = _load_match(catalog, {"type": "sourcetype", "id": sourcetype_id, "label": ""})
            for uc_id in _neighbor_ids(other, "uses", "in"):
                scores[uc_id] += 3
        return scores
    if kind == "cimDataset":
        for sourcetype_id in _neighbor_ids(doc, "mapsTo", "in"):
            other = _load_match(catalog, {"type": "sourcetype", "id": sourcetype_id, "label": ""})
            for uc_id in _neighbor_ids(other, "uses", "in"):
                scores[uc_id] += 3
        return scores
    predicate = {
        "industry": "inIndustry",
        "businessOutcome": "servesOutcome",
        "businessArea": "inArea",
        "persona": "forPersona",
        "complianceControl": "covers",
    }.get(kind)
    if predicate:
        for uc_id in _neighbor_ids(doc, predicate, "in"):
            scores[uc_id] += 1
    return scores


def find_related_use_cases(
    *,
    catalog: Catalog,
    entity_id: str,
    entity_type: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Use cases that share sourcetypes or vendor products with an entity.

    Shared sourcetypes count 3 and shared vendor products count 2. The
    query use case is left out. Ties break on the use-case id.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("limit must be an integer from 1 to 50")
    doc = get_entity(catalog=catalog, entity_id=entity_id, entity_type=entity_type)
    if doc.get("ambiguous"):
        raise ValueError("alias matches more than one entity; pass entity_type")
    scores = _related_ids(catalog, doc)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]
    use_cases = []
    for uc_id, score in ranked:
        label = uc_id
        try:
            uc = _load_match(catalog, {"type": "usecase", "id": uc_id, "label": ""})
            label = uc.get("label") or uc_id
        except CatalogNotFoundError:
            label = uc_id
        use_cases.append({"id": uc_id, "score": score, "label": label})
    return {
        "entity": {"id": doc["id"], "type": doc["type"], "label": doc.get("label") or doc["id"]},
        "count": len(use_cases),
        "useCases": use_cases,
    }
