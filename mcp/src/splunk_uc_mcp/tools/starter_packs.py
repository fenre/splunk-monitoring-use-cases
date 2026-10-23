"""Guided-onboarding tools: ``list_starter_packs``, ``get_starter_pack``,
``plan_rollout``.

Starter packs (``api/v1/starter-packs/``) are short, ordered lists of
existing use cases for one goal (security or operations) and one
technology. Drafts are hidden unless the caller passes
``include_drafts=True``, matching the "Start here" wizard on the site.
``plan_rollout`` runs the same planner as the wizard
(:mod:`splunk_uc_mcp.starter_plan`), so an agent and the browser give the
same answer for the same inputs.
"""

from __future__ import annotations

import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError
from splunk_uc_mcp.starter_plan import LEVELS, MAX_STEPS
from splunk_uc_mcp.starter_plan import parse_paste as _parse_paste
from splunk_uc_mcp.starter_plan import plan_rollout as _plan_rollout

PACK_ID_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
_PACK_ID_REGEX = re.compile(PACK_ID_PATTERN)
_EQUIPMENT_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9_]*$")
_GOALS = ("security", "operations")
_MAX_LIST_ITEMS = 1000
_MAX_NAME_LENGTH = 200
_MAX_PASTE_CHARS = 200_000

_STRING_LIST = {
    "type": "array",
    "items": {"type": "string", "maxLength": _MAX_NAME_LENGTH},
    "maxItems": _MAX_LIST_ITEMS,
}

_INCLUDE_DRAFTS = {
    "type": "boolean",
    "description": (
        "Include packs that are still in curation (status=draft). Defaults "
        "to false, matching the site wizard."
    ),
    "default": False,
}


LIST_STARTER_PACKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "goal": {
            "type": "string",
            "enum": list(_GOALS),
            "description": "Only packs for this goal.",
        },
        "equipment_id": {
            "type": "string",
            "description": (
                "Only packs that apply to this equipment slug or compound "
                "model id (e.g. 'windows', 'cisco_catalyst_center')."
            ),
            "pattern": _EQUIPMENT_ID_REGEX.pattern,
        },
        "include_drafts": _INCLUDE_DRAFTS,
    },
    "additionalProperties": False,
}

_PACK_SUMMARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "title", "goal", "status", "equipment", "stepCount"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "goal": {"type": "string", "enum": list(_GOALS)},
        "status": {"type": "string", "enum": ["draft", "published"]},
        "pairId": {"type": ["string", "null"]},
        "equipment": {"type": "array", "items": {"type": "string"}},
        "stepCount": {"type": "integer", "minimum": 0},
        "nextPacks": {"type": "array", "items": {"type": "string"}},
        "publishable": {"type": "boolean"},
        "url": {"type": "string"},
    },
}

LIST_STARTER_PACKS_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "packs"],
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "packs": {"type": "array", "items": _PACK_SUMMARY_SCHEMA},
    },
}


GET_STARTER_PACK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["pack_id"],
    "properties": {
        "pack_id": {
            "type": "string",
            "description": "Pack id from list_starter_packs (e.g. 'windows-security-basics').",
            "pattern": PACK_ID_PATTERN,
        },
        "include_drafts": _INCLUDE_DRAFTS,
    },
    "additionalProperties": False,
}

GET_STARTER_PACK_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "title", "goal", "status", "requiredData", "steps"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "goal": {"type": "string", "enum": list(_GOALS)},
        "status": {"type": "string", "enum": ["draft", "published"]},
        "pairId": {"type": ["string", "null"]},
        "equipment": {"type": "array", "items": {"type": "string"}},
        "requiredData": {
            "type": "object",
            "properties": {
                "splunkbaseApps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "displayName": {"type": "string"},
                        },
                    },
                },
                "sourcetypes": {"type": "array", "items": {"type": "string"}},
                "indexes": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
            },
        },
        "industrySources": {"type": "array", "items": {"type": "object"}},
        "nextPacks": {"type": "array", "items": {"type": "string"}},
        "stepCount": {"type": "integer"},
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["order", "ucId", "title"],
                "properties": {
                    "order": {"type": "integer"},
                    "ucId": {"type": "string"},
                    "title": {"type": "string"},
                    "criticality": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "wave": {"type": "string"},
                    "status": {"type": ["string", "null"]},
                    "prerequisiteUseCases": {"type": "array", "items": {"type": "string"}},
                    "sourcetypes": {"type": "array", "items": {"type": "string"}},
                    "indexes": {"type": "array", "items": {"type": "string"}},
                    "url": {"type": "string"},
                    "json": {"type": "string"},
                    "markdown": {"type": "string"},
                },
            },
        },
        "readiness": {"type": "object"},
        "url": {"type": "string"},
    },
}


PLAN_ROLLOUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["goal"],
    "properties": {
        "goal": {
            "type": "string",
            "enum": list(_GOALS),
            "description": "What the user wants first: catch attackers or keep things running.",
        },
        "level": {
            "type": "string",
            "enum": list(LEVELS),
            "description": (
                "Self-reported Splunk experience. Only adds a "
                "difficultyWarning flag to harder steps; nothing is hidden."
            ),
            "default": "beginner",
        },
        "sourcetypes": {
            **_STRING_LIST,
            "description": (
                "Sourcetypes already in the user's Splunk (e.g. from "
                "'| tstats count where (index=* OR index=_*) by index, "
                "sourcetype'). Case-insensitive; documented aliases such "
                "as WinEventLog/XmlWinEventLog are merged."
            ),
        },
        "indexes": {
            **_STRING_LIST,
            "description": "Indexes the user can search (internal ones like _internal matter for platform packs).",
        },
        "equipment": {
            **_STRING_LIST,
            "description": "Equipment slugs or compound model ids the user owns (see list_equipment).",
        },
        "paste": {
            "type": "string",
            "maxLength": _MAX_PASTE_CHARS,
            "description": (
                "Raw pasted tstats output, CSV, or a plain list. Parsed "
                "the same way as the site wizard and merged with "
                "sourcetypes / indexes."
            ),
        },
        "include_drafts": _INCLUDE_DRAFTS,
        "max_steps": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_STEPS,
            "default": MAX_STEPS,
        },
    },
    "additionalProperties": False,
}

PLAN_ROLLOUT_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["goal", "level", "packs", "steps", "nextSources", "emptyReason"],
    "properties": {
        "goal": {"type": "string", "enum": list(_GOALS)},
        "level": {"type": "string", "enum": list(LEVELS)},
        "packs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "unlock", "readySteps", "totalSteps"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                    "unlock": {"type": "string", "enum": ["full", "partial", "none"]},
                    "readySteps": {"type": "integer"},
                    "totalSteps": {"type": "integer"},
                    "equipmentMatch": {"type": "boolean"},
                    "missingData": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "steps": {
            "type": "array",
            "maxItems": MAX_STEPS,
            "items": {
                "type": "object",
                "required": ["position", "ucId", "packId", "ready", "difficultyWarning"],
                "properties": {
                    "position": {"type": "integer"},
                    "ucId": {"type": "string"},
                    "title": {"type": "string"},
                    "packId": {"type": "string"},
                    "order": {"type": "integer"},
                    "criticality": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "wave": {"type": "string"},
                    "ready": {"type": "boolean"},
                    "difficultyWarning": {"type": "boolean"},
                },
            },
        },
        "nextSources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["kind", "name", "unlocks", "packs"],
                "properties": {
                    "kind": {"type": "string", "enum": ["sourcetype", "index"]},
                    "name": {"type": "string"},
                    "unlocks": {"type": "integer"},
                    "packs": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "emptyReason": {"type": ["string", "null"], "enum": [None, "no-input", "no-match"]},
        "parsed": {
            "type": "object",
            "description": "What was extracted from `paste`, when supplied.",
            "properties": {
                "sourcetypes": {"type": "array", "items": {"type": "string"}},
                "indexes": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


def _check_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean (got {type(value).__name__})")
    return value


def _check_goal(goal: Any, *, required: bool) -> str | None:
    if goal is None and not required:
        return None
    if goal not in _GOALS:
        raise ValueError(f"goal must be one of {list(_GOALS)}: {goal!r}")
    return str(goal)


def _check_string_list(name: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list of strings")
    if len(value) > _MAX_LIST_ITEMS:
        raise ValueError(f"{name} accepts at most {_MAX_LIST_ITEMS} items")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or len(item) > _MAX_NAME_LENGTH:
            raise ValueError(f"{name} items must be strings of at most {_MAX_NAME_LENGTH} chars")
        out.append(item)
    return out


def _load_index(catalog: Catalog) -> dict[str, Any]:
    index = catalog.load_json("starter-packs", "index.json")
    if not isinstance(index, dict):
        raise CatalogNotFoundError("starter-packs/index.json is not an object")
    return index


def _summary(pack: dict[str, Any]) -> dict[str, Any]:
    readiness = pack.get("readiness") or {}
    return {
        "id": pack.get("id"),
        "title": pack.get("title"),
        "description": pack.get("description", ""),
        "goal": pack.get("goal"),
        "status": pack.get("status"),
        "pairId": pack.get("pairId"),
        "equipment": list(pack.get("equipment") or []),
        "stepCount": int(pack.get("stepCount") or len(pack.get("steps") or [])),
        "nextPacks": list(pack.get("nextPacks") or []),
        "publishable": bool(readiness.get("publishable", False)),
        "url": pack.get("url", ""),
    }


def _equipment_applies(pack_equipment: list[str], equipment_id: str) -> bool:
    return any(equipment_id == e or equipment_id.startswith(e + "_") for e in pack_equipment)


def list_starter_packs(
    *,
    catalog: Catalog,
    goal: str | None = None,
    equipment_id: str | None = None,
    include_drafts: bool = False,
) -> dict[str, Any]:
    """List starter packs, published only unless ``include_drafts``."""

    goal = _check_goal(goal, required=False)
    include_drafts = _check_bool("include_drafts", include_drafts)
    if equipment_id is not None and not _EQUIPMENT_ID_REGEX.fullmatch(str(equipment_id)):
        raise ValueError(f"equipment_id must match {_EQUIPMENT_ID_REGEX.pattern}: {equipment_id!r}")

    out: list[dict[str, Any]] = []
    for pack in _load_index(catalog).get("packs") or []:
        if pack.get("status") != "published" and not include_drafts:
            continue
        if goal is not None and pack.get("goal") != goal:
            continue
        if equipment_id is not None and not _equipment_applies(
            list(pack.get("equipment") or []), equipment_id
        ):
            continue
        out.append(_summary(pack))
    out.sort(key=lambda p: str(p["id"]))
    return {"count": len(out), "packs": out}


def get_starter_pack(
    *,
    catalog: Catalog,
    pack_id: str,
    include_drafts: bool = False,
) -> dict[str, Any]:
    """Return one pack with its resolved, ordered steps."""

    include_drafts = _check_bool("include_drafts", include_drafts)
    if not isinstance(pack_id, str) or not _PACK_ID_REGEX.fullmatch(pack_id):
        raise ValueError(f"pack_id must match {PACK_ID_PATTERN}: {pack_id!r}")
    doc = catalog.load_json("starter-packs", f"{pack_id}.json")
    pack = doc.get("pack") if isinstance(doc, dict) else None
    if not isinstance(pack, dict):
        raise CatalogNotFoundError(f"Starter pack {pack_id} not found")
    if pack.get("status") != "published" and not include_drafts:
        raise CatalogNotFoundError(
            f"Starter pack {pack_id} is a draft; pass include_drafts=true to read it"
        )
    return {k: v for k, v in pack.items() if k != "curationNotes" and not k.startswith("$")}


def plan_rollout(
    *,
    catalog: Catalog,
    goal: str,
    level: str = "beginner",
    sourcetypes: list[str] | None = None,
    indexes: list[str] | None = None,
    equipment: list[str] | None = None,
    paste: str | None = None,
    include_drafts: bool = False,
    max_steps: int = MAX_STEPS,
) -> dict[str, Any]:
    """Return an ordered starter plan (max 10 steps) for the user's data."""

    checked_goal = _check_goal(goal, required=True)
    if level not in LEVELS:
        raise ValueError(f"level must be one of {list(LEVELS)}: {level!r}")
    include_drafts = _check_bool("include_drafts", include_drafts)
    if (
        not isinstance(max_steps, int)
        or isinstance(max_steps, bool)
        or not 1 <= max_steps <= MAX_STEPS
    ):
        raise ValueError(f"max_steps must be an integer between 1 and {MAX_STEPS}")
    st = _check_string_list("sourcetypes", sourcetypes)
    ix = _check_string_list("indexes", indexes)
    eq = _check_string_list("equipment", equipment)

    parsed: dict[str, list[str]] | None = None
    if paste is not None:
        if not isinstance(paste, str) or len(paste) > _MAX_PASTE_CHARS:
            raise ValueError(f"paste must be a string of at most {_MAX_PASTE_CHARS} chars")
        parsed = _parse_paste(paste)
        st = st + parsed["sourcetypes"]
        ix = ix + parsed["indexes"]

    result = _plan_rollout(
        _load_index(catalog),
        goal=checked_goal,
        level=level,
        sourcetypes=st,
        indexes=ix,
        equipment=eq,
        include_drafts=include_drafts,
        max_steps=max_steps,
    )
    if parsed is not None:
        result["parsed"] = parsed
    return result
