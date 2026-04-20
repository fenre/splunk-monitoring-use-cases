"""Equipment-centric tools: ``list_equipment`` + ``get_equipment``.

Phase 5.5 introduced the structured equipment layer
(``api/v1/equipment/index.json`` + ``api/v1/equipment/{slug}.json``).
These tools are thin wrappers so agents can reason about deployment
stacks ("I have Azure + Palo Alto + ServiceNow") without pulling the
whole 6,424-UC list.
"""

from __future__ import annotations

import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog


EQUIPMENT_ID_PATTERN = r"^[a-z0-9][a-z0-9_]*$"


LIST_EQUIPMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "regulation_id": {
            "type": "string",
            "description": (
                "Only return equipment that has at least one UC tagged "
                "against this regulation. Useful when the agent wants to "
                "know which tech stack matters for a specific framework."
            ),
            "pattern": r"^[a-z0-9][a-z0-9\-]*$",
        },
        "min_use_case_count": {
            "type": "integer",
            "description": (
                "Lower bound on the equipment's total UC count. Defaults "
                "to 0 (no filter)."
            ),
            "minimum": 0,
            "default": 0,
        },
    },
    "additionalProperties": False,
}


LIST_EQUIPMENT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "equipment"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "equipment": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "label", "useCaseCount"],
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "useCaseCount": {"type": "integer", "minimum": 0},
                    "complianceUseCaseCount": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "regulationIds": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "models": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                            },
                        },
                    },
                    "endpoint": {"type": "string"},
                },
            },
        },
    },
}


GET_EQUIPMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["equipment_id"],
    "properties": {
        "equipment_id": {
            "type": "string",
            "description": (
                "Lowercase slug (e.g. 'azure', 'paloalto', 'cisco_ise', "
                "'servicenow'). Enumerable via list_equipment()."
            ),
            "pattern": EQUIPMENT_ID_PATTERN,
        },
    },
    "additionalProperties": False,
}


GET_EQUIPMENT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "label"],
    "properties": {
        "id": {"type": "string"},
        "label": {"type": "string"},
        "useCaseCount": {"type": "integer"},
        "complianceUseCaseCount": {"type": "integer"},
        "models": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "modelId": {"type": "string"},
                    "useCaseCount": {"type": "integer"},
                    "useCaseIds": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "useCaseIds": {"type": "array", "items": {"type": "string"}},
        "useCasesByCategory": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": ["string", "integer"]},
                    "useCaseCount": {"type": "integer"},
                    "useCaseIds": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "regulationIds": {"type": "array", "items": {"type": "string"}},
        "regulations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "regulationId": {"type": "string"},
                    "regulationEndpoint": {"type": "string"},
                    "useCaseCount": {"type": "integer"},
                    "useCaseIds": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "clauseMappings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "clause": {"type": "string"},
                                "useCaseId": {"type": "string"},
                                "version": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    },
}


_EQUIPMENT_ID_REGEX = re.compile(EQUIPMENT_ID_PATTERN)
_REGULATION_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


def list_equipment(
    *,
    catalog: Catalog,
    regulation_id: str | None = None,
    min_use_case_count: int = 0,
) -> dict[str, Any]:
    """Return the equipment overview with optional filters.

    The ``regulation_id`` filter reuses the precomputed
    ``regulationIds`` array on each equipment entry, so no per-equipment
    JSON load is required.
    """

    if not isinstance(min_use_case_count, int) or isinstance(min_use_case_count, bool):
        raise ValueError(
            f"min_use_case_count must be an integer (got "
            f"{type(min_use_case_count).__name__})"
        )
    if min_use_case_count < 0:
        raise ValueError("min_use_case_count must be >= 0")
    if regulation_id is not None and not _REGULATION_ID_REGEX.fullmatch(regulation_id):
        raise ValueError(
            f"regulation_id must match {_REGULATION_ID_REGEX.pattern}: "
            f"{regulation_id!r}"
        )

    index = catalog.load_json("equipment", "index.json")
    items: list[dict[str, Any]] = index.get("equipment", [])

    out: list[dict[str, Any]] = []
    for item in items:
        if item.get("useCaseCount", 0) < min_use_case_count:
            continue
        if regulation_id is not None:
            if regulation_id not in (item.get("regulationIds") or []):
                continue
        out.append(item)

    return {"count": len(out), "equipment": out}


def get_equipment(
    *,
    catalog: Catalog,
    equipment_id: str,
) -> dict[str, Any]:
    """Return full detail for an equipment slug.

    Includes UCs grouped by category and, for compliance-tagged UCs,
    regulation → clause mappings.
    """

    if not _EQUIPMENT_ID_REGEX.fullmatch(equipment_id):
        raise ValueError(
            f"equipment_id must match {EQUIPMENT_ID_PATTERN}: {equipment_id!r}"
        )
    doc = catalog.load_json("equipment", f"{equipment_id}.json")
    return _strip_meta(doc)


def _strip_meta(doc: dict[str, Any]) -> dict[str, Any]:
    """Remove generator bookkeeping so agents see only curated fields."""

    drop = {"apiVersion", "generatedAt", "catalogueVersion", "indexEndpoint"}
    return {k: v for k, v in doc.items() if k not in drop and not k.startswith("$")}
