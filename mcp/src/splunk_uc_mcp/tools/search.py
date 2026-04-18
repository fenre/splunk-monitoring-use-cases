"""``search_use_cases`` tool — keyword + metadata filter over the catalogue.

Reads ``api/v1/recommender/uc-thin.json`` (the 6,424-UC compact index) and
applies a series of AND filters. Case-insensitive keyword matching over the
title and value fields is provided to keep the agent prompt concise.

Serves both personas:

* **Compliance officers** filter by ``regulation_id`` (passed through to
  ``get_use_case`` for per-UC compliance detail).
* **Detection engineers** filter by ``category`` (primary taxonomy) plus
  ``equipment`` for the stack they actually have.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog


LOG = logging.getLogger(__name__)


_CATEGORY_PATTERN = re.compile(r"^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$")
"""Primary category id or ``category.subcategory`` pair (e.g. ``22`` or
``22.1``). The tool splits on the first dot to decide which filter to
apply."""

_REGULATION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]*$")
_EQUIPMENT_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_MITRE_PATTERN = re.compile(r"^T\d{4}(\.\d{3})?$")
_QUERY_MAX_LEN = 200


SEARCH_MAX_LIMIT = 100
"""Upper bound on the response size. The CoSAI MCP guidance recommends
capping tool output to avoid DoS; 100 UCs is ample for an agent's
context window and keeps the payload under 100 KB."""


SEARCH_DEFAULT_LIMIT = 20
"""Default :func:`search_use_cases` limit when the caller does not
specify one — chosen to fit comfortably in an agent's context alongside
the follow-up ``get_use_case`` call."""


SEARCH_USE_CASES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": (
                "Case-insensitive keyword. Matches against title and value "
                "(each UC's short business description). Leave empty to "
                "enumerate without text filtering."
            ),
            "maxLength": 200,
        },
        "category": {
            "type": "string",
            "description": (
                "Primary category id (e.g. '22' for compliance) or "
                "'category.subcategory' pair (e.g. '22.1'). Matches against "
                "the leading segments of the UC id."
            ),
            "pattern": r"^(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))?$",
        },
        "regulation_id": {
            "type": "string",
            "description": (
                "Kebab-case regulation slug (e.g. 'gdpr', 'hipaa-security'). "
                "Forces a secondary lookup against /api/v1/compliance/ucs/ "
                "to keep only UCs whose compliance[] array cites this "
                "regulation."
            ),
            "pattern": "^[a-z0-9][a-z0-9\\-]*$",
        },
        "equipment": {
            "type": "string",
            "description": (
                "Equipment slug (e.g. 'azure', 'paloalto'). Filters UCs "
                "whose equipment[] contains this id."
            ),
            "pattern": "^[a-z0-9][a-z0-9_]*$",
        },
        "mitre_technique": {
            "type": "string",
            "description": (
                "MITRE ATT&CK technique ID (e.g. 'T1566', 'T1566.001'). "
                "Filters UCs whose mitreAttack[] contains this id."
            ),
            "pattern": "^T\\d{4}(\\.\\d{3})?$",
        },
        "limit": {
            "type": "integer",
            "description": (
                f"Maximum number of results (default {SEARCH_DEFAULT_LIMIT}, "
                f"hard-capped at {SEARCH_MAX_LIMIT})."
            ),
            "minimum": 1,
            "maximum": SEARCH_MAX_LIMIT,
            "default": SEARCH_DEFAULT_LIMIT,
        },
    },
    "additionalProperties": False,
}


SEARCH_USE_CASES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "truncated", "useCases"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "totalMatched": {"type": "integer", "minimum": 0},
        "truncated": {"type": "boolean"},
        "useCases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "value": {"type": "string"},
                    "criticality": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "splunkPillar": {"type": "string"},
                    "monitoringType": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "app": {"type": "array", "items": {"type": "string"}},
                    "equipment": {"type": "array", "items": {"type": "string"}},
                    "equipmentModels": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "mitreAttack": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "cimModels": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}


def search_use_cases(
    *,
    catalog: Catalog,
    query: str | None = None,
    category: str | None = None,
    regulation_id: str | None = None,
    equipment: str | None = None,
    mitre_technique: str | None = None,
    limit: int = SEARCH_DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Search the use-case catalogue with AND-composed filters.

    Every parameter is optional — an unfiltered call returns the first
    ``limit`` UCs, which is rarely useful but preserves the "enumerate
    cheaply" affordance.

    :class:`ValueError` is raised if ``limit`` is outside ``[1, 100]``; the
    schema already clamps it but agents sometimes ignore schemas.
    """

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(f"limit must be an integer (got {type(limit).__name__})")
    if limit < 1 or limit > SEARCH_MAX_LIMIT:
        raise ValueError(
            f"limit must be in [1, {SEARCH_MAX_LIMIT}] (got {limit})"
        )
    if query is not None:
        if not isinstance(query, str):
            raise ValueError(
                f"query must be a string (got {type(query).__name__})"
            )
        if len(query) > _QUERY_MAX_LEN:
            raise ValueError(
                f"query must be <= {_QUERY_MAX_LEN} chars (got {len(query)})"
            )
    if category is not None and not _CATEGORY_PATTERN.fullmatch(category):
        raise ValueError(
            f"category must match {_CATEGORY_PATTERN.pattern}: {category!r}"
        )
    if regulation_id is not None and not _REGULATION_PATTERN.fullmatch(regulation_id):
        raise ValueError(
            f"regulation_id must match {_REGULATION_PATTERN.pattern}: {regulation_id!r}"
        )
    if equipment is not None and not _EQUIPMENT_PATTERN.fullmatch(equipment):
        raise ValueError(
            f"equipment must match {_EQUIPMENT_PATTERN.pattern}: {equipment!r}"
        )
    if mitre_technique is not None and not _MITRE_PATTERN.fullmatch(mitre_technique):
        raise ValueError(
            f"mitre_technique must match {_MITRE_PATTERN.pattern}: {mitre_technique!r}"
        )

    thin = catalog.load_json("recommender", "uc-thin.json")
    use_cases: list[dict[str, Any]] = thin.get("useCases", [])

    # Pre-compute the compliance filter set (much faster than per-UC loads).
    regulation_allow: set[str] | None = None
    if regulation_id:
        regulation_allow = _load_ucs_for_regulation(catalog, regulation_id)

    q_lower = query.lower().strip() if query else None
    results: list[dict[str, Any]] = []
    matched_total = 0

    for uc in use_cases:
        if category and not _uc_in_category(uc["id"], category):
            continue
        if equipment and equipment not in (uc.get("equipment") or []):
            continue
        if mitre_technique and mitre_technique not in (uc.get("mitreAttack") or []):
            continue
        if regulation_allow is not None and uc["id"] not in regulation_allow:
            continue
        if q_lower and not _keyword_match(uc, q_lower):
            continue

        matched_total += 1
        if len(results) < limit:
            results.append(_slim_uc(uc))

    return {
        "count": len(results),
        "totalMatched": matched_total,
        "truncated": matched_total > len(results),
        "useCases": results,
    }


def _uc_in_category(uc_id: str, category: str) -> bool:
    """Match UC id against ``category`` (primary only) or a dotted
    ``category.subcategory`` prefix (e.g. ``22.1``)."""

    parts = uc_id.split(".")
    target = category.split(".")
    return parts[: len(target)] == target


def _keyword_match(uc: dict[str, Any], q_lower: str) -> bool:
    """Substring match against title + value. Intentionally simple — no
    tokenisation, no stemming; the agent's prompt handles semantics."""

    haystacks = (uc.get("title", ""), uc.get("value", ""))
    return any(q_lower in s.lower() for s in haystacks)


def _slim_uc(uc: dict[str, Any]) -> dict[str, Any]:
    """Project only the fields present in uc-thin so we don't accidentally
    leak fields that haven't been audited for agent consumption."""

    keys = (
        "id",
        "title",
        "value",
        "criticality",
        "difficulty",
        "splunkPillar",
        "monitoringType",
        "app",
        "equipment",
        "equipmentModels",
        "mitreAttack",
        "cimModels",
    )
    return {k: uc[k] for k in keys if k in uc}


def _load_ucs_for_regulation(catalog: Catalog, regulation_id: str) -> set[str]:
    """Return the set of UC IDs that reference ``regulation_id``.

    Uses the precomputed ``regulationIds`` field on the compliance-ucs
    index, which stores entries in ``"{slug}@{version}"`` form. We match
    by slug prefix so the caller can reference the regulation without
    knowing the specific version string.
    """

    index = catalog.load_json("compliance", "ucs", "index.json")
    items: list[dict[str, Any]] = index.get("items", [])
    matched: set[str] = set()
    for item in items:
        for reg_id in item.get("regulationIds", []):
            if reg_id.split("@", 1)[0] == regulation_id:
                matched.add(item["id"])
                break
    LOG.debug(
        "Regulation %s resolves to %d UCs out of %d compliance-tagged",
        regulation_id,
        len(matched),
        len(items),
    )
    return matched
