"""Compliance-gap tools: surface uncovered clauses per regulation and
expose the clause-first story layer so agents can answer "which clause
covers what" without re-deriving the mapping.

Three tools live here:

* :func:`find_compliance_gap` — reads the pre-computed gap analysis at
  ``api/v1/compliance/gaps.json`` and narrows it to the regulations the
  caller cares about, with an optional ``equipment_id`` overlay.
* :func:`get_clause_coverage` — returns the clause-first coverage entry
  (top assurance, covering UCs, obligation text, endpoint) for a single
  ``regulationId`` + ``clause``. Reads
  ``api/v1/compliance/clauses/index.json``.
* :func:`list_uncovered_clauses` — lists every clause whose
  ``coverageState`` is ``not-authored`` for one or more regulations,
  sorted by descending ``priorityWeight`` so the agent can prioritise
  remediation.

Everything is derived from the catalogue's own JSON — we never re-compute
the gap logic here to guarantee the MCP and the site report the same
numbers.
"""

from __future__ import annotations

import re
from typing import Any

from splunk_uc_mcp.catalog import Catalog, CatalogNotFoundError


REGULATION_ID_PATTERN = r"^[a-z0-9][a-z0-9\-]*$"
EQUIPMENT_ID_PATTERN = r"^[a-z0-9][a-z0-9_]*$"
# Clause labels come straight from the regulator and may contain section
# signs (§), mid-dot, slashes, parentheses, and whitespace. We keep the
# regex permissive-but-capped: printable characters only, plus the
# commonly-used obligation markers. This is a caller-facing allow-list
# only — the filename slug used by the `clauses/` endpoint family is
# built server-side via URL-encoding so the value never reaches the
# filesystem unescaped.
CLAUSE_PATTERN = r"^[A-Za-z0-9§\-\._/()\[\]\s&,]+$"
CLAUSE_MAX_LENGTH = 64


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


# =====================================================================
# Story-layer tools — added in v1.6.x alongside the clauses reverse index.
# =====================================================================


_CLAUSE_REGEX = re.compile(CLAUSE_PATTERN)


GET_CLAUSE_COVERAGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["regulation_id", "clause"],
    "properties": {
        "regulation_id": {
            "type": "string",
            "description": "Kebab-case regulation slug (e.g. 'gdpr').",
            "pattern": REGULATION_ID_PATTERN,
        },
        "clause": {
            "type": "string",
            "description": (
                "Clause label exactly as it appears in the regulator text "
                "(e.g. 'Art.5', '§164.312(a)(1)', '8.2.1'). Comparison is "
                "exact; callers must not URL-encode or otherwise rewrite "
                "the value."
            ),
            "minLength": 1,
            "maxLength": CLAUSE_MAX_LENGTH,
            "pattern": CLAUSE_PATTERN,
        },
        "version": {
            "type": "string",
            "description": (
                "Optional regulation version label (e.g. '2016/679'). When "
                "the regulation ships only one active version this is "
                "ignored; when multiple versions exist and no label is "
                "given, we pick the version that actually has this clause "
                "authored (first match wins)."
            ),
            "maxLength": 64,
        },
    },
    "additionalProperties": False,
}


GET_CLAUSE_COVERAGE_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["regulationId", "clause", "clauseId", "coverageState"],
    "properties": {
        "regulationId": {"type": "string"},
        "regulationShortName": {"type": "string"},
        "clause": {"type": "string"},
        "clauseId": {
            "type": "string",
            "description": (
                "Canonical identifier of the form "
                "``regulationId@version#clause`` — stable across builds."
            ),
        },
        "version": {"type": "string"},
        "tier": {"type": "integer"},
        "topic": {"type": ["string", "null"]},
        "priorityWeight": {"type": ["number", "null"]},
        "coverageState": {
            "type": "string",
            "enum": [
                "covered-full",
                "covered-partial",
                "contributing-only",
                "uncovered",
                "unknown",
            ],
        },
        "topAssurance": {"type": ["string", "null"]},
        "assuranceBreakdown": {
            "type": "object",
            "properties": {
                "full": {"type": "integer"},
                "partial": {"type": "integer"},
                "contributing": {"type": "integer"},
                "unknown": {"type": "integer"},
            },
        },
        "coveringUcs": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Use-case IDs (e.g. '22.1.1') that cite this clause. "
                "Pass any entry to ``get_use_case`` for full detail."
            ),
        },
        "coveringUcCount": {"type": "integer"},
        "obligationTextPresent": {"type": "boolean"},
        "clauseEndpoint": {
            "type": "string",
            "description": (
                "Relative URL of the per-clause JSON endpoint "
                "(``/api/v1/compliance/clauses/{slug}.json``). Clients "
                "that want the full payload can dereference it."
            ),
        },
        "deepLink": {
            "type": "string",
            "description": (
                "Relative URL that opens the clause in the browser-side "
                "clause navigator — useful when an agent wants to cite "
                "a human-readable view."
            ),
        },
    },
}


LIST_UNCOVERED_CLAUSES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["regulations"],
    "properties": {
        "regulations": {
            "type": "array",
            "description": (
                "One or more regulation slugs to inspect. Use '*' as a "
                "single-element shortcut to scan every regulation in the "
                "clauses index."
            ),
            "items": {
                "type": "string",
                "pattern": r"^(\*|[a-z0-9][a-z0-9\-]*)$",
            },
            "minItems": 1,
            "maxItems": 20,
        },
        "tier": {
            "type": "integer",
            "description": (
                "Optional tier filter (1..3). Applied after the regulation "
                "filter; useful to focus on tier-1 baselines."
            ),
            "minimum": 1,
            "maximum": 3,
        },
        "include_common_only": {
            "type": "boolean",
            "description": (
                "When true, restrict to clauses that appear on the "
                "``commonClauses`` list for their regulation. Defaults to "
                "false so callers also see uncovered bespoke clauses."
            ),
        },
        "limit": {
            "type": "integer",
            "description": (
                "Cap the number of entries returned. Defaults to 50; the "
                "maximum is 500 to keep payloads bounded even for "
                "cross-framework sweeps."
            ),
            "minimum": 1,
            "maximum": 500,
        },
    },
    "additionalProperties": False,
}


LIST_UNCOVERED_CLAUSES_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["count", "entries", "summary"],
    "properties": {
        "count": {"type": "integer"},
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "regulationId",
                    "clause",
                    "clauseId",
                    "coverageState",
                ],
                "properties": {
                    "regulationId": {"type": "string"},
                    "regulationShortName": {"type": "string"},
                    "version": {"type": "string"},
                    "tier": {"type": "integer"},
                    "clause": {"type": "string"},
                    "clauseId": {"type": "string"},
                    "topic": {"type": ["string", "null"]},
                    "priorityWeight": {"type": ["number", "null"]},
                    "onCommonList": {"type": "boolean"},
                    "coverageState": {"type": "string"},
                    "obligationTextPresent": {"type": "boolean"},
                    "clauseEndpoint": {"type": "string"},
                    "deepLink": {"type": "string"},
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
                "totalUncoveredInScope": {"type": "integer"},
                "truncated": {"type": "boolean"},
                "limit": {"type": "integer"},
            },
        },
    },
}


def get_clause_coverage(
    *,
    catalog: Catalog,
    regulation_id: str,
    clause: str,
    version: str | None = None,
) -> dict[str, Any]:
    """Return the clause-first coverage entry for a single regulator clause.

    The payload mirrors the shape used by the clause-navigator UI so
    agents can reason about coverage without re-deriving it:

    * ``coverageState`` — one of ``covered-full``, ``covered-partial``,
      ``contributing-only``, ``uncovered``, ``unknown``.
    * ``coveringUcs`` — UC IDs the agent can pass to
      :func:`get_use_case` for the full SPL + implementation detail.
    * ``deepLink`` — relative URL that opens the clause in the browser
      clause navigator.

    Raises :class:`ValueError` on malformed input and
    :class:`~splunk_uc_mcp.catalog.CatalogNotFoundError` when the clause
    is not listed in the catalogue's reverse index.
    """

    if not isinstance(regulation_id, str) or not re.fullmatch(
        REGULATION_ID_PATTERN, regulation_id
    ):
        raise ValueError(
            f"regulation_id must match {REGULATION_ID_PATTERN}: {regulation_id!r}"
        )
    if not isinstance(clause, str) or not clause.strip():
        raise ValueError("clause must be a non-empty string")
    if len(clause) > CLAUSE_MAX_LENGTH:
        raise ValueError(
            f"clause must be <= {CLAUSE_MAX_LENGTH} characters (got {len(clause)})"
        )
    if not _CLAUSE_REGEX.fullmatch(clause):
        raise ValueError(
            f"clause contains characters not on the allow-list: {clause!r}"
        )
    if version is not None:
        if not isinstance(version, str):
            raise ValueError(
                f"version must be a string (got {type(version).__name__})"
            )
        if len(version) > 64:
            raise ValueError(
                f"version must be <= 64 characters (got {len(version)})"
            )

    index = catalog.load_json("compliance", "clauses", "index.json")
    entries: list[dict[str, Any]] = [
        c for c in index.get("clauses", [])
        if c.get("regulationId") == regulation_id and c.get("clause") == clause
    ]
    if not entries:
        raise CatalogNotFoundError(
            f"No clause {clause!r} found for regulation {regulation_id!r}"
        )

    if version is not None:
        match = next((c for c in entries if c.get("version") == version), None)
        if match is None:
            available = sorted({c.get("version", "") for c in entries})
            raise CatalogNotFoundError(
                f"Clause {clause!r} is not authored in regulation "
                f"{regulation_id!r} version {version!r} "
                f"(available versions: {', '.join(filter(None, available)) or 'none'})"
            )
    else:
        # Prefer the version that actually has a non-empty coveringUcs
        # list so the default answer is always the actionable one.
        match = next(
            (c for c in entries if c.get("coveringUcs")),
            entries[0],
        )

    return _project_clause_entry(match)


def list_uncovered_clauses(
    *,
    catalog: Catalog,
    regulations: list[str],
    tier: int | None = None,
    include_common_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """List every clause whose ``coverageState == 'uncovered'`` for the
    requested regulations, sorted by descending priority weight then
    regulation/clause so the output is deterministic.

    "Uncovered" means the catalogue has no use-case authored against the
    clause. Clauses with ``contributing-only`` coverage are technically
    present and therefore excluded from this worklist — use
    :func:`find_compliance_gap` when the caller wants weaker coverage
    included.

    Pass ``regulations=['*']`` to sweep across every regulation in the
    clauses index. ``tier`` scopes to one regulatory tier (1..3) and
    ``include_common_only=True`` restricts to commonClauses-listed
    clauses. ``limit`` caps the returned entries (default 50, max 500);
    ``summary.truncated`` signals whether more matches were suppressed.
    """

    if not isinstance(regulations, list) or not regulations:
        raise ValueError("regulations must be a non-empty list")
    if len(regulations) > 20:
        raise ValueError("regulations accepts at most 20 ids per call")
    wildcard = regulations == ["*"]
    if not wildcard:
        for rid in regulations:
            if (
                not isinstance(rid, str)
                or not re.fullmatch(REGULATION_ID_PATTERN, rid)
            ):
                raise ValueError(
                    f"regulation id must match {REGULATION_ID_PATTERN}: {rid!r}"
                )
    if tier is not None:
        if not isinstance(tier, int) or isinstance(tier, bool):
            raise ValueError(f"tier must be an integer (got {type(tier).__name__})")
        if tier < 1 or tier > 3:
            raise ValueError(f"tier must be in [1, 3] (got {tier})")
    if not isinstance(include_common_only, bool):
        raise ValueError(
            f"include_common_only must be boolean (got {type(include_common_only).__name__})"
        )
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError(f"limit must be an integer (got {type(limit).__name__})")
    if limit < 1 or limit > 500:
        raise ValueError(f"limit must be in [1, 500] (got {limit})")

    index = catalog.load_json("compliance", "clauses", "index.json")
    all_clauses = index.get("clauses", [])

    requested = set() if wildcard else set(regulations)
    resolved: set[str] = set()
    matches: list[dict[str, Any]] = []

    for entry in all_clauses:
        rid = entry.get("regulationId")
        if not rid:
            continue
        if not wildcard and rid not in requested:
            continue
        if entry.get("coverageState") != "uncovered":
            # Presence guard: only list truly-uncovered clauses. A
            # ``contributing-only`` clause is NOT surfaced here because
            # at least one UC is already writing to it.
            # Callers who want weaker coverage included should use
            # ``find_compliance_gap`` or inspect the clauses index
            # directly.
            continue
        if tier is not None and entry.get("tier") != tier:
            continue
        if include_common_only and not _is_common_clause(entry):
            # Today every entry in ``clauses/index.json`` is sourced from
            # ``commonClauses[]`` so the filter is effectively a no-op
            # against production data. We keep the parameter so a future
            # generator that also indexes bespoke clauses can honour it
            # without breaking backwards compatibility.
            continue
        resolved.add(rid)
        matches.append(_project_matrix_entry(entry))

    matches.sort(
        key=lambda m: (
            -(m.get("priorityWeight") or 0.0),
            m.get("regulationId") or "",
            m.get("clause") or "",
        )
    )

    not_found = [] if wildcard else sorted(requested - resolved)
    total = len(matches)
    truncated = total > limit

    return {
        "count": min(total, limit),
        "entries": matches[:limit],
        "summary": {
            "regulationsRequested": (
                len(all_clauses) if wildcard else len(requested)
            ),
            "regulationsResolved": len(resolved),
            "regulationsNotFound": not_found,
            "totalUncoveredInScope": total,
            "truncated": truncated,
            "limit": limit,
        },
    }


# ---------------------------------------------------------------------
# Projection helpers — one point of truth for field selection so the
# tool output stays in sync with the catalogue's clauses index even as
# the underlying generator gains columns.
# ---------------------------------------------------------------------


def _is_common_clause(entry: dict[str, Any]) -> bool:
    """Best-effort detection of a ``commonClauses``-sourced entry.

    The catalogue's clauses index does not emit an explicit
    ``onCommonList`` flag yet, but clauses sourced from
    ``commonClauses[]`` always carry ``priorityWeight`` + ``topic``.
    That signal is adopted here so :func:`list_uncovered_clauses` can
    honour ``include_common_only`` today without touching the indexer.
    """

    if "onCommonList" in entry:
        return bool(entry["onCommonList"])
    return entry.get("priorityWeight") is not None and bool(entry.get("topic"))


def _project_clause_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Return the ``get_clause_coverage`` response for an index entry."""

    clause_id = entry.get("clauseId")
    endpoint = entry.get("endpoint")
    deep_link: str | None = None
    if clause_id:
        from urllib.parse import quote

        # The clause-navigator page accepts the full clauseId as-is
        # (``#clause=<urlencoded>``); we URL-encode to guard against
        # unusual clause labels without forcing the caller to encode.
        deep_link = f"clause-navigator.html#clause={quote(clause_id, safe='')}"

    out: dict[str, Any] = {
        "regulationId": entry.get("regulationId"),
        "regulationShortName": entry.get("regulationShortName"),
        "clause": entry.get("clause"),
        "clauseId": clause_id,
        "version": entry.get("version"),
        "tier": entry.get("tier"),
        "topic": entry.get("topic"),
        "priorityWeight": entry.get("priorityWeight"),
        "coverageState": entry.get("coverageState") or "unknown",
        "topAssurance": entry.get("topAssurance"),
        "assuranceBreakdown": entry.get("assuranceBreakdown") or {},
        "coveringUcs": list(entry.get("coveringUcs") or []),
        "coveringUcCount": entry.get("coveringUcCount") or 0,
        "obligationTextPresent": bool(entry.get("obligationTextPresent")),
    }
    if endpoint:
        out["clauseEndpoint"] = endpoint
    if deep_link:
        out["deepLink"] = deep_link
    # Strip keys whose value is None so the JSON payload stays compact
    # and the MCP output-schema validator sees only the fields we can
    # actually guarantee.
    return {k: v for k, v in out.items() if v is not None}


def _project_matrix_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Return the ``list_uncovered_clauses`` row for an index entry."""

    clause_id = entry.get("clauseId")
    endpoint = entry.get("endpoint")
    deep_link: str | None = None
    if clause_id:
        from urllib.parse import quote

        deep_link = f"clause-navigator.html#clause={quote(clause_id, safe='')}"

    row: dict[str, Any] = {
        "regulationId": entry.get("regulationId"),
        "regulationShortName": entry.get("regulationShortName"),
        "version": entry.get("version"),
        "tier": entry.get("tier"),
        "clause": entry.get("clause"),
        "clauseId": clause_id,
        "topic": entry.get("topic"),
        "priorityWeight": entry.get("priorityWeight"),
        "onCommonList": _is_common_clause(entry),
        "coverageState": entry.get("coverageState") or "unknown",
        "obligationTextPresent": bool(entry.get("obligationTextPresent")),
    }
    if endpoint:
        row["clauseEndpoint"] = endpoint
    if deep_link:
        row["deepLink"] = deep_link
    return {k: v for k, v in row.items() if v is not None}
