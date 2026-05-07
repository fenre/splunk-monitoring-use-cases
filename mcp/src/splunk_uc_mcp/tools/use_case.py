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


GET_USE_CASE_MARKDOWN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["uc_id"],
    "properties": {
        "uc_id": {
            "type": "string",
            "description": (
                "Three-part dotted UC ID (same shape as get_use_case). "
                "Returns a plain-markdown rendering of the UC instead of "
                "the structured JSON document — drop directly into a "
                "system prompt or RAG context with no field-mapping work."
            ),
            "pattern": UC_ID_PATTERN,
        },
    },
    "additionalProperties": False,
}


GET_USE_CASE_MARKDOWN_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["id", "markdown", "url"],
    "properties": {
        "id": {
            "type": "string",
            "description": "Canonical UC ID with prefix (``UC-X.Y.Z``).",
        },
        "url": {
            "type": "string",
            "description": (
                "Stable canonical URL of the markdown twin "
                "(``/uc/UC-X.Y.Z/uc.md``)."
            ),
        },
        "markdown": {
            "type": "string",
            "description": (
                "Plain-markdown rendering of the use case (no HTML, no "
                "JSON). Includes title, plain-language summary, quick-"
                "facts table, prerequisites, value, SPL, implementation, "
                "false positives, MITRE / regulations, and references."
            ),
        },
        "lastModified": {
            "type": "string",
            "description": (
                "ISO-8601 date of the last review (when set on the UC) "
                "or the build timestamp otherwise."
            ),
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
        out = _strip_meta(detail)
        # Guarantee array-typed fields are always arrays. Non-compliance
        # UCs (cat-1 … cat-21) carry no compliance metadata, and UCs
        # without upstream dependencies carry no prerequisiteUseCases,
        # but the output schema declares both as arrays so clients can
        # call ``len()`` without a ``None`` check.
        out.setdefault("compliance", [])
        out.setdefault("prerequisiteUseCases", [])
        return out
    except CatalogNotFoundError:
        LOG.debug("get_use_case %s: no compliance sidecar, falling back to uc-thin", uc_id)

    thin = catalog.load_json("recommender", "uc-thin.json")
    for uc in thin.get("useCases", []):
        if uc.get("id") == uc_id:
            out = dict(uc)
            out.setdefault("compliance", [])
            out.setdefault("prerequisiteUseCases", [])
            return out

    raise CatalogNotFoundError(f"Use case {uc_id} not found in catalogue")


def get_use_case_markdown(*, catalog: Catalog, uc_id: str) -> dict[str, Any]:
    """Return the LLM-friendly plain-markdown twin for one UC.

    Mirrors the static-site artefact at ``/uc/UC-X.Y.Z/uc.md`` byte-for-
    byte: same headings, same quick-facts table, same trailing source
    line. Agents that prefer plain text over JSON can drop the result
    straight into a system prompt or RAG chunk without any field-
    mapping logic.

    Implementation note: we re-use :func:`get_use_case` to load the UC
    dict and then synthesise the markdown locally. This keeps the MCP
    server self-contained (no dependency on the build pipeline) and
    means the output is always up-to-date with the catalogue version
    the server was started with — even if no static site has been
    rebuilt since.
    """

    uc = get_use_case(catalog=catalog, uc_id=uc_id)

    site_url = "https://fenre.github.io/splunk-monitoring-use-cases"
    full_id = f"UC-{uc_id}"
    md_url = f"{site_url}/uc/{full_id}/uc.md"
    canonical_html = f"{site_url}/uc/{full_id}/"
    json_url = f"{site_url}/uc/{full_id}/index.json"

    title = str(uc.get("title") or full_id)
    last_modified = str(uc.get("reviewed") or "").strip()

    lines: list[str] = []
    lines.append(f"# {full_id} — {title}")
    lines.append("")
    lines.append(
        f"> Canonical HTML: {canonical_html}  ·  JSON twin: {json_url}"
    )
    if last_modified:
        lines.append(f"> Last-modified: {last_modified}")
    lines.append("")

    ge = str(uc.get("grandmaExplanation") or uc.get("ge") or "").strip()
    if ge:
        lines.append("## In plain language")
        lines.append("")
        lines.append(f"> {ge}")
        lines.append("")

    facts: list[tuple[str, str]] = []

    def _add_fact(label: str, raw: Any) -> None:
        if raw is None or raw == "" or raw == [] or raw == {}:
            return
        if isinstance(raw, (list, tuple)):
            value = ", ".join(str(v) for v in raw if v not in (None, ""))
        else:
            value = str(raw).strip()
        if not value:
            return
        # Pipe characters in markdown table cells need escaping; collapse
        # newlines so single rows stay on one logical line.
        value = value.replace("|", "\\|").replace("\n", " ")
        facts.append((label, value))

    _add_fact("Criticality", uc.get("criticality"))
    _add_fact("Difficulty", uc.get("difficulty"))
    _add_fact("Wave", uc.get("wave"))
    _add_fact("Pillar", uc.get("splunkPillar") or uc.get("pillar"))
    _add_fact("Monitoring type", uc.get("monitoringType"))
    _add_fact("App / TA", uc.get("app"))
    _add_fact("Data sources", uc.get("dataSources"))
    _add_fact("CIM models", uc.get("cimModels"))
    _add_fact("Equipment", uc.get("equipment"))
    _add_fact("Equipment models", uc.get("equipmentModels"))
    _add_fact("MITRE ATT&CK", uc.get("mitreAttack"))
    _add_fact("Last reviewed", uc.get("reviewed"))

    if facts:
        lines.append("## Quick facts")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        for label, value in facts:
            lines.append(f"| {label} | {value} |")
        lines.append("")

    pre = uc.get("prerequisiteUseCases") or []
    if isinstance(pre, list) and pre:
        lines.append("## Prerequisite use cases")
        lines.append("")
        for p in pre:
            p_str = str(p).strip()
            if not p_str:
                continue
            short = p_str[3:] if p_str.startswith("UC-") else p_str
            lines.append(f"- [{p_str}]({site_url}/uc/UC-{short}/)")
        lines.append("")

    def _add_text_section(heading: str, raw: Any) -> None:
        text = str(raw or "").strip()
        if not text:
            return
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(text)
        lines.append("")

    def _add_code_section(heading: str, raw: Any, lang: str = "spl") -> None:
        text = str(raw or "").strip()
        if not text:
            return
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(f"```{lang}")
        lines.append(text)
        lines.append("```")
        lines.append("")

    _add_text_section("Value", uc.get("value"))
    _add_code_section("SPL", uc.get("spl"))
    _add_code_section("CIM SPL (tstats)", uc.get("cimSpl"))
    _add_text_section(
        "Implementation",
        uc.get("detailedImplementation") or uc.get("implementation"),
    )
    _add_text_section("Visualization", uc.get("visualization"))

    kfp = uc.get("knownFalsePositives")
    if kfp:
        lines.append("## Known false positives")
        lines.append("")
        if isinstance(kfp, (list, tuple)):
            for item in kfp:
                if str(item).strip():
                    lines.append(f"- {str(item).strip()}")
        else:
            lines.append(str(kfp).strip())
        lines.append("")

    refs = uc.get("references") or []
    if isinstance(refs, list) and refs:
        lines.append("## References")
        lines.append("")
        for r in refs:
            if isinstance(r, dict):
                t = str(r.get("title") or "").strip()
                u = str(r.get("url") or "").strip()
                if t and u:
                    lines.append(f"- [{t}]({u})")
                elif u:
                    lines.append(f"- {u}")
                elif t:
                    lines.append(f"- {t}")
            else:
                r_str = str(r).strip()
                if r_str:
                    lines.append(f"- {r_str}")
        lines.append("")

    compl = uc.get("compliance") or []
    if isinstance(compl, list) and compl:
        lines.append("## Compliance mappings")
        lines.append("")
        for c in compl:
            if not isinstance(c, dict):
                continue
            reg = str(c.get("regulation") or "").strip()
            clause = str(c.get("clause") or "").strip()
            mode = str(c.get("mode") or "").strip()
            assurance = str(c.get("assurance") or "").strip()
            extras: list[str] = []
            if mode:
                extras.append(f"mode: {mode}")
            if assurance:
                extras.append(f"assurance: {assurance}")
            tail = f" ({'; '.join(extras)})" if extras else ""
            if reg and clause:
                lines.append(f"- {reg} — {clause}{tail}")
            elif reg:
                lines.append(f"- {reg}{tail}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"Source: [Splunk Monitoring Use Cases]({site_url}/) — "
        f"licensed MIT. UC-IDs are stable; see "
        f"[/llms.txt]({site_url}/llms.txt) for the catalogue index "
        f"and [/AGENTS.md]({site_url}/AGENTS.md) for the agent "
        f"entrypoint."
    )
    lines.append("")

    return {
        "id": full_id,
        "url": md_url,
        "markdown": "\n".join(lines),
        "lastModified": last_modified,
    }


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
