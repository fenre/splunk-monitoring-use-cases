"""UC-centric tools: ``get_use_case`` + ``list_categories``.

``get_use_case`` serves both personas in one call:

* **Compliance officers** rely on the full ``compliance[]`` array
  (regulation, clause, mode, assurance, rationale) plus the
  signed-ledger provenance status.
* **Detection engineers** rely on the ``spl`` field, ``implementation``
  notes, ``references``, ``dataSources``, ``mitreAttack``, and
  ``knownFalsePositives``.

Nothing is projected away, because (a) the underlying JSON is already
the curated, per-UC view the site publishes, and (b) hiding fields
would force a two-call dance for users who want both perspectives.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError


LOG = logging.getLogger(__name__)


UC_ID_PATTERN = r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"


GET_USE_CASE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["uc_id"],
    "properties": {
        "uc_id": {
            "type": "string",
            "description": (
                "Three-part dotted UC ID, e.g. '22.1.1' (GDPR PII "
                "detection), '9.4.3' (network), '1.1.65' (Linux). The "
                "catalogue never uses leading zeros."
            ),
            "pattern": UC_ID_PATTERN,
        },
    },
    "additionalProperties": False,
}


GET_USE_CASE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "title"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "value": {"type": "string"},
        "criticality": {"type": "string"},
        "difficulty": {"type": "string"},
        "wave": {
            "type": "string",
            "description": (
                "Implementation wave — ``crawl`` (foundation), ``walk`` "
                "(intermediate), or ``run`` (advanced). Empty string when "
                "the UC has not been assigned a wave."
            ),
        },
        "prerequisiteUseCases": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": r"^UC-(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$",
            },
            "description": (
                "UC IDs (``UC-X.Y.Z``) that must be implemented before "
                "this one — data sources, macros, lookups, or upstream "
                "detections this UC depends on."
            ),
        },
        "splunkPillar": {"type": "string"},
        "monitoringType": {"type": "array", "items": {"type": "string"}},
        "app": {"type": ["string", "array"]},
        "equipment": {"type": "array", "items": {"type": "string"}},
        "equipmentModels": {"type": "array", "items": {"type": "string"}},
        "mitreAttack": {"type": "array", "items": {"type": "string"}},
        "cimModels": {"type": "array", "items": {"type": "string"}},
        "dataSources": {"type": "string"},
        "spl": {"type": "string"},
        "cimSpl": {"type": "string"},
        "implementation": {"type": "string"},
        "knownFalsePositives": {"type": "string"},
        "visualization": {"type": "string"},
        "references": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
        },
        "compliance": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "regulation": {"type": "string"},
                    "regulationId": {"type": "string"},
                    "version": {"type": "string"},
                    "clause": {"type": "string"},
                    "clauseUrl": {"type": "string"},
                    "mode": {"type": "string"},
                    "assurance": {"type": "string"},
                    "assurance_rationale": {"type": "string"},
                    "provenance": {"type": "string"},
                },
            },
        },
    },
}


LIST_CATEGORIES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {},
}


LIST_CATEGORIES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "categories"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "useCaseCount"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "useCaseCount": {"type": "integer", "minimum": 0},
                    "subcategories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "useCaseCount": {
                                    "type": "integer",
                                    "minimum": 0,
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


_UC_ID_REGEX = re.compile(UC_ID_PATTERN)


def get_use_case(*, catalog: Catalog, uc_id: str) -> dict[str, Any]:
    """Return full detail for a single UC.

    The return shape depends on whether the UC has a compliance sidecar:
    cat-22 UCs return the richer ``api/v1/compliance/ucs/{id}.json``
    document; other UCs return the compact record from ``uc-thin.json``
    (same fields as the search result, plus a ``compliance`` key that is
    always ``[]`` for non-cat-22 UCs).

    Raises :class:`ValueError` on a malformed ID and
    :class:`~splunk_uc_mcp.catalog.CatalogNotFoundError` when the UC
    does not exist in the catalogue.
    """

    if not _UC_ID_REGEX.fullmatch(uc_id):
        raise ValueError(f"uc_id must match {UC_ID_PATTERN}: {uc_id!r}")

    try:
        detail = catalog.load_json("compliance", "ucs", f"{uc_id}.json")
        LOG.debug("get_use_case %s: using compliance sidecar", uc_id)
        return _strip_meta(detail)
    except CatalogNotFoundError:
        LOG.debug("get_use_case %s: no compliance sidecar, falling back to uc-thin", uc_id)

    thin = catalog.load_json("recommender", "uc-thin.json")
    for uc in thin.get("useCases", []):
        if uc.get("id") == uc_id:
            out = dict(uc)
            out.setdefault("compliance", [])
            return out

    raise CatalogNotFoundError(f"Use case {uc_id} not found in catalogue")


def list_categories(*, catalog: Catalog) -> dict[str, Any]:
    """Return the category tree with UC counts per subcategory.

    Derived from ``uc-thin.json`` so the counts reflect the total
    catalogue (6,424 UCs across 23 categories), not just the 1,340
    compliance-tagged ones.
    """

    thin = catalog.load_json("recommender", "uc-thin.json")
    use_cases: list[dict[str, Any]] = thin.get("useCases", [])

    # Group by cat.sub.uc → build {cat: {sub: count}}.
    tree: dict[str, dict[str, int]] = {}
    for uc in use_cases:
        uc_id = uc.get("id") or ""
        parts = uc_id.split(".")
        if len(parts) < 3:
            continue
        cat_id, sub_id = parts[0], f"{parts[0]}.{parts[1]}"
        tree.setdefault(cat_id, {}).setdefault(sub_id, 0)
        tree[cat_id][sub_id] += 1

    categories: list[dict[str, Any]] = []
    for cat_id in sorted(tree, key=lambda x: int(x)):
        sub_map = tree[cat_id]
        cat_total = sum(sub_map.values())
        subs = [
            {
                "id": sid,
                "useCaseCount": count,
            }
            for sid, count in sorted(
                sub_map.items(),
                key=lambda kv: tuple(int(p) for p in kv[0].split(".")),
            )
        ]
        categories.append(
            {
                "id": cat_id,
                "useCaseCount": cat_total,
                "subcategories": subs,
            }
        )

    return {
        "count": len(categories),
        "categories": categories,
    }


def _strip_meta(doc: dict[str, Any]) -> dict[str, Any]:
    """Remove schema bookkeeping keys so the tool response is LLM-friendly."""

    out = {k: v for k, v in doc.items() if not k.startswith("$")}
    out.pop("_meta", None)
    out.pop("apiVersion", None)
    return out
