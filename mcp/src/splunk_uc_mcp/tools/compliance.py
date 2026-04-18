"""Compliance-gap tool: surface uncovered clauses per regulation.

Reads the pre-computed gap analysis at ``api/v1/compliance/gaps.json`` and
narrows it to the regulations the caller cares about. When
``equipment_id`` is supplied we also intersect against the equipment's
own ``clauseMappings`` so the agent can answer questions like:

    "I have Azure + Palo Alto. Which HIPAA §164.312 controls do I still
    have zero coverage for?"

Everything is derived — we never re-compute the gap logic here to
guarantee the MCP and the site report the same numbers.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError


LOG = logging.getLogger(__name__)


REGULATION_ID_PATTERN = r"^[a-z0-9][a-z0-9\-]*$"
EQUIPMENT_ID_PATTERN = r"^[a-z0-9][a-z0-9_]*$"


FIND_COMPLIANCE_GAP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["regulations"],
    "properties": {
        "regulations": {
            "type": "array",
            "description": (
                "Regulations to evaluate. Each entry is a kebab-case slug "
                "(e.g. 'gdpr', 'hipaa-security')."
            ),
            "items": {
                "type": "string",
                "pattern": REGULATION_ID_PATTERN,
            },
            "minItems": 1,
            "maxItems": 20,
        },
        "equipment_id": {
            "type": "string",
            "description": (
                "Optional equipment filter. When provided, the response "
                "flags which of each regulation's uncovered clauses are "
                "already hit by at least one UC tagged to this equipment."
            ),
            "pattern": EQUIPMENT_ID_PATTERN,
        },
    },
    "additionalProperties": False,
}


FIND_COMPLIANCE_GAP_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["entries", "summary"],
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["regulationId"],
                "properties": {
                    "regulationId": {"type": "string"},
                    "regulation": {"type": "string"},
                    "version": {"type": "string"},
                    "tier": {"type": "integer"},
                    "commonClausesTotal": {"type": "integer"},
                    "commonClausesCovered": {"type": "integer"},
                    "commonClausesUncovered": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "commonClausesUncoveredCount": {"type": "integer"},
                    "priorityWeightedUncovered": {"type": "number"},
                    "regulationEndpoint": {"type": "string"},
                    "equipmentOverlay": {
                        "type": "object",
                        "description": (
                            "Only populated when equipment_id is supplied. "
                            "clausesCoveredByEquipment lists the clauses "
                            "within this regulation that have at least one "
                            "UC bearing the equipment tag."
                        ),
                        "properties": {
                            "equipmentId": {"type": "string"},
                            "clausesCoveredByEquipment": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "uncoveredClausesStillUncovered": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "summary": {
            "type": "object",
            "properties": {
                "regulationsRequested": {"type": "integer"},
                "regulationsResolved": {"type": "integer"},
                "regulationsNotFound": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "totalUncoveredClauses": {"type": "integer"},
                "equipmentId": {"type": "string"},
            },
        },
    },
}


_REGULATION_ID_REGEX = re.compile(REGULATION_ID_PATTERN)
_EQUIPMENT_ID_REGEX = re.compile(EQUIPMENT_ID_PATTERN)


def find_compliance_gap(
    *,
    catalog: Catalog,
    regulations: list[str],
    equipment_id: str | None = None,
) -> dict[str, Any]:
    """Return the pre-computed gap entries for ``regulations``.

    The optional ``equipment_id`` parameter adds a per-regulation overlay
    so an agent can immediately see how the caller's existing stack
    intersects the unclosed clauses.
    """

    if not isinstance(regulations, list):
        raise ValueError(
            f"regulations must be a list (got {type(regulations).__name__})"
        )
    if not regulations:
        raise ValueError("regulations must contain at least one id")
    if len(regulations) > 20:
        raise ValueError("regulations accepts at most 20 ids per call")
    for rid in regulations:
        if not isinstance(rid, str) or not _REGULATION_ID_REGEX.fullmatch(rid):
            raise ValueError(
                f"regulation id must match {REGULATION_ID_PATTERN}: {rid!r}"
            )
    if equipment_id is not None and not _EQUIPMENT_ID_REGEX.fullmatch(equipment_id):
        raise ValueError(
            f"equipment_id must match {EQUIPMENT_ID_PATTERN}: {equipment_id!r}"
        )

    gaps = catalog.load_json("compliance", "gaps.json")
    by_id = {entry["regulationId"]: entry for entry in gaps.get("entries", [])}

    equipment_doc: dict[str, Any] | None = None
    if equipment_id is not None:
        try:
            equipment_doc = catalog.load_json("equipment", f"{equipment_id}.json")
        except CatalogNotFoundError:
            raise CatalogNotFoundError(
                f"Equipment {equipment_id} is not in /api/v1/equipment/ index"
            ) from None

    out_entries: list[dict[str, Any]] = []
    not_found: list[str] = []
    total_uncovered = 0

    for rid in regulations:
        entry = by_id.get(rid)
        if entry is None:
            not_found.append(rid)
            continue
        projected = dict(entry)
        total_uncovered += len(entry.get("commonClausesUncovered", []))

        if equipment_doc is not None:
            overlay = _equipment_overlay(equipment_doc, rid, entry)
            projected["equipmentOverlay"] = overlay

        out_entries.append(projected)

    summary: dict[str, Any] = {
        "regulationsRequested": len(regulations),
        "regulationsResolved": len(out_entries),
        "regulationsNotFound": not_found,
        "totalUncoveredClauses": total_uncovered,
    }
    if equipment_id is not None:
        summary["equipmentId"] = equipment_id

    return {"entries": out_entries, "summary": summary}


def _equipment_overlay(
    equipment_doc: dict[str, Any],
    regulation_id: str,
    gap_entry: dict[str, Any],
) -> dict[str, Any]:
    """Produce the ``equipmentOverlay`` block for a single regulation.

    The equipment JSON ships ``regulations[].regulationId`` directly — we
    use that for matching. If a legacy document omits it we fall back to
    parsing the ``regulationEndpoint`` URL (``/{id}.json`` or
    ``/{id}@{ver}.json``).
    """

    covered: set[str] = set()
    for reg in equipment_doc.get("regulations", []):
        reg_id = reg.get("regulationId")
        if not reg_id:
            endpoint = reg.get("regulationEndpoint") or ""
            reg_id = endpoint.rsplit("/", 1)[-1].split(".", 1)[0].split("@", 1)[0]
        if reg_id != regulation_id:
            continue
        for mapping in reg.get("clauseMappings", []):
            clause = mapping.get("clause")
            if clause:
                covered.add(clause)

    uncovered = set(gap_entry.get("commonClausesUncovered", []))
    still_uncovered = sorted(uncovered - covered)

    return {
        "equipmentId": equipment_doc.get("id"),
        "clausesCoveredByEquipment": sorted(covered),
        "uncoveredClausesStillUncovered": still_uncovered,
    }
