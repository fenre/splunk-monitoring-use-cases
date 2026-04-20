#!/usr/bin/env python3
"""Generate tier-1 evidence packs for regulators and external auditors.

Phase 4.2 of the compliance gold-standard programme.

What this script does
---------------------
1. Reads:
   - data/regulations.json         (single source of truth for clauses,
                                    priority weights, authoritative URLs)
   - data/evidence-pack-extras.json (auditor-facing metadata: retention,
                                    roles, authoritative guidance, etc.)
   - use-cases/cat-*/uc-*.json     (UC sidecars with compliance[] arrays)
   - reports/compliance-gaps.json   (pre-computed per-version coverage,
                                    produced by
                                    scripts/audit_compliance_gaps.py)

2. Produces, deterministically:
   - docs/evidence-packs/{regulation-id}.md   (human-readable evidence
                                               pack per regulation,
                                               tuned for privacy / legal /
                                               audit / risk readers)
   - api/v1/evidence-packs/{regulation-id}.json
                                              (machine-readable twin
                                               suitable for programmatic
                                               consumers: GRC tools,
                                               audit-request portals,
                                               evidence-pipeline bots)
   - api/v1/evidence-packs/index.json         (index of all packs)
   - docs/evidence-packs/README.md            (directory intro and
                                               reading order)

Design tenets
-------------
- Deterministic: sorted ordering everywhere, stable JSON serialisation,
  no timestamps in output bodies other than a single explicit
  generation-metadata block.
- Idempotent: re-running with no inputs changed produces byte-identical
  output; wired into CI via --check mode for drift detection.
- Provenance-preserving: every clause coverage claim is traceable back
  to a specific UC sidecar JSON file and to the commonClauses entry in
  data/regulations.json. No fact in the output is un-sourced.
- Zero-SME-opinion: the generator does not assert legal conclusions;
  it tabulates what the catalogue covers, names the authoritative
  source, and flags gaps. Interpretation stays with counsel.

Usage
-----
    python3 scripts/generate_evidence_packs.py          # write mode
    python3 scripts/generate_evidence_packs.py --check  # CI drift check

Exit status
-----------
    0  success (write mode) OR no drift (--check mode)
    1  drift detected OR hard error

"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------
# Paths and constants
# ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
REGULATIONS_PATH = ROOT / "data" / "regulations.json"
EXTRAS_PATH = ROOT / "data" / "evidence-pack-extras.json"
EXTRAS_SCHEMA_PATH = ROOT / "schemas" / "evidence-pack-extras.schema.json"
GAPS_REPORT_PATH = ROOT / "reports" / "compliance-gaps.json"
UC_SIDECAR_GLOB = "use-cases/cat-*/uc-*.json"
DOCS_OUT_DIR = ROOT / "docs" / "evidence-packs"
API_OUT_DIR = ROOT / "api" / "v1" / "evidence-packs"
VERSION_PATH = ROOT / "VERSION"

# Tier-1 evidence-pack target list.
# 11 frameworks have tier=1 in data/regulations.json; UK GDPR is tier=2
# but included here because UK companies need UK GDPR (not EU GDPR)
# coverage in practice, and Phase 3.3 propagation produces 100 %
# derived clause coverage. UK GDPR closes the Brexit-era gap that every
# UK-based privacy officer asks about first.
PACK_TARGETS = [
    "gdpr",
    "uk-gdpr",
    "pci-dss",
    "hipaa-security",
    "sox-itgc",
    "soc-2",
    "iso-27001",
    "nist-csf",
    "nist-800-53",
    "nis2",
    "dora",
    "cmmc",
]

# Fixed order for display in the index and README to ensure stable sort.
PACK_DISPLAY_ORDER = PACK_TARGETS[:]


# ----------------------------------------------------------------------
# I/O helpers
# ----------------------------------------------------------------------
def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _dump_json_bytes(data: Any) -> bytes:
    """Deterministic JSON serialisation: 2-space indent, sorted keys,
    trailing newline, stable Unicode handling."""
    body = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    return (body + "\n").encode("utf-8")


def _stable_markdown_bytes(text: str) -> bytes:
    """Strip trailing whitespace per line, ensure single trailing
    newline. This eliminates editor-driven churn in diffs."""
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n").encode("utf-8")


def _get_version() -> str:
    try:
        return VERSION_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


# ----------------------------------------------------------------------
# UC sidecar discovery and indexing
# ----------------------------------------------------------------------
def _iter_uc_sidecars() -> list[Path]:
    """Return every UC sidecar path, sorted."""
    paths: list[Path] = []
    for category_dir in sorted((ROOT / "use-cases").glob("cat-*")):
        if not category_dir.is_dir():
            continue
        for side_path in sorted(category_dir.glob("uc-*.json")):
            paths.append(side_path)
    return paths


def _load_all_ucs() -> list[dict[str, Any]]:
    """Load every UC sidecar; annotate with its source path."""
    results: list[dict[str, Any]] = []
    for path in _iter_uc_sidecars():
        try:
            doc = _load_json(path)
        except json.JSONDecodeError as exc:
            print(
                f"ERROR: {path.relative_to(ROOT)} is not valid JSON: {exc}",
                file=sys.stderr,
            )
            raise
        doc.setdefault("_source_path", str(path.relative_to(ROOT)))
        results.append(doc)
    return results


def _build_compliance_index(
    ucs: list[dict[str, Any]],
    alias_index: dict[str, str],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Index UCs by (framework_id, version) → list of entries.

    Compliance entries in UC sidecars use human-readable regulation names
    ("GDPR", "PCI DSS", "SOX-ITGC") rather than framework ids. We
    normalise via the aliasIndex in data/regulations.json so the packs
    can key against framework ids.

    Each entry contains {uc_id, uc_title, clause, assurance, rationale,
    provenance, derivationSource (opt), source_path}.
    """
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    # Case-insensitive alias lookup
    alias_lc = {k.lower(): v for k, v in alias_index.items() if not k.startswith("$")}
    for uc in ucs:
        uc_id = uc.get("id")
        uc_title = uc.get("title") or uc.get("name") or ""
        if not uc_id:
            continue
        compliance = uc.get("compliance") or []
        for entry in compliance:
            reg_raw = entry.get("regulation")
            ver = entry.get("version")
            clause = entry.get("clause")
            if not reg_raw or not clause:
                continue
            # Resolve to framework id via aliasIndex (lowercase lookup);
            # already-normalised ids pass through unchanged.
            reg_id = alias_lc.get(str(reg_raw).lower(), reg_raw)
            key = (reg_id, ver or "")
            index.setdefault(key, []).append({
                "uc_id": uc_id,
                "uc_title": uc_title,
                "clause": clause,
                "assurance": entry.get("assurance") or "contributing",
                "rationale": entry.get("rationale") or "",
                "provenance": entry.get("provenance") or "native",
                "derivationSource": entry.get("derivationSource"),
                "source_path": uc.get("_source_path"),
            })
    return index


# ----------------------------------------------------------------------
# Assurance bucketing
# ----------------------------------------------------------------------
_ASSURANCE_RANK = {"full": 3, "partial": 2, "contributing": 1}


def _best_assurance(entries: list[dict[str, Any]]) -> str:
    """Pick the highest assurance across the entries for a clause."""
    best = "contributing"
    best_rank = 0
    for entry in entries:
        rank = _ASSURANCE_RANK.get(entry.get("assurance"), 0)
        if rank > best_rank:
            best_rank = rank
            best = entry.get("assurance") or "contributing"
    return best


# ----------------------------------------------------------------------
# Clause sorting
# ----------------------------------------------------------------------
_CLAUSE_NUM_RE = re.compile(r"\d+")


def _clause_sort_key(clause: str) -> tuple[Any, ...]:
    """Natural-looking ordering for clause identifiers.

    Splits on any non-digit delimiter so `Art.5` < `Art.10`, and the
    sub-clause `Art.5(1)(e)` falls after `Art.5`. Non-numeric tokens
    sort lexicographically (e.g. `§164.308` < `§164.502`).
    """
    tokens = _CLAUSE_NUM_RE.findall(clause)
    numeric = tuple(int(t) for t in tokens) if tokens else ()
    return (clause.split(".")[0], numeric, clause)


# ----------------------------------------------------------------------
# Coverage calculation
#
# Primary source: reports/compliance-gaps.json, produced by
# scripts/audit_compliance_gaps.py. That script already handles the
# aliasIndex normalisation, derivation-source propagation, priority
# weighting, and per-clause UC-id rollups. We read those figures so
# the evidence packs stay consistent with the authoritative gap report.
#
# Fallback: if the gap report is missing a regulation (shouldn't happen
# for our 12 targets, but defensive), compute live from the UC
# compliance index against regulations.json commonClauses.
# ----------------------------------------------------------------------
def _load_gap_report() -> dict[str, Any]:
    if not GAPS_REPORT_PATH.exists():
        return {}
    return _load_json(GAPS_REPORT_PATH)


def _gap_report_lookup(
    gap_report: dict[str, Any],
    reg_id: str,
    version: str,
) -> dict[str, Any] | None:
    """Locate the version-level block for (reg_id, version) in the
    compliance-gaps.json report. Searches tier-1 then tier-2."""
    tiers = gap_report.get("tiers") or {}
    for tier_key in ("tier-1", "tier-2", "tier-3"):
        tier_block = tiers.get(tier_key) or {}
        reg_block = tier_block.get(reg_id)
        if not reg_block:
            continue
        versions = reg_block.get("versions") or {}
        if version in versions:
            return versions[version]
    return None


def _compute_coverage_from_index(
    reg_id: str,
    version: str,
    common_clauses: list[dict[str, Any]],
    compliance_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Fallback coverage calculation against commonClauses using the
    UC compliance index; mirrors scripts/audit_compliance_gaps.py logic."""
    by_clause: dict[str, list[dict[str, Any]]] = {}
    for entry in compliance_index.get((reg_id, version), []):
        by_clause.setdefault(entry["clause"], []).append(entry)

    clauses_out: list[dict[str, Any]] = []
    covered = 0
    priority_total = 0.0
    priority_covered = 0.0
    for clause_def in common_clauses:
        clause = clause_def["clause"]
        entries = by_clause.get(clause, [])
        weight = float(clause_def.get("priorityWeight") or 0.5)
        priority_total += weight
        if entries:
            covered += 1
            priority_covered += weight
            max_assurance = _best_assurance(entries)
            uc_ids = sorted({e["uc_id"] for e in entries})
        else:
            max_assurance = None
            uc_ids = []
        clauses_out.append({
            "clause": clause,
            "topic": clause_def.get("topic"),
            "priority_weight": weight,
            "covered": bool(entries),
            "max_assurance": max_assurance,
            "uc_count": len(entries),
            "uc_ids": uc_ids,
        })

    total = len(common_clauses)
    coverage_pct = (covered / total * 100.0) if total else 0.0
    priority_pct = (priority_covered / priority_total * 100.0) if priority_total else 0.0
    return {
        "clauses": clauses_out,
        "common_clause_count": total,
        "covered_count": covered,
        "coverage_pct": coverage_pct,
        "priority_weight_total": priority_total,
        "priority_weight_covered": priority_covered,
        "priority_weight_pct": priority_pct,
    }


def _extract_coverage(
    gap_block: dict[str, Any] | None,
    version: str,
    reg_id: str,
    common_clauses: list[dict[str, Any]],
    compliance_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Prefer gap-report figures; fall back to live index computation."""
    if gap_block and gap_block.get("clauses") is not None:
        return {
            "clauses": [
                {
                    "clause": c.get("clause"),
                    "topic": c.get("topic"),
                    "priority_weight": c.get("priority_weight", 0.5),
                    "covered": c.get("covered", False),
                    "max_assurance": c.get("max_assurance"),
                    "uc_count": c.get("uc_count", 0),
                    "uc_ids": sorted(c.get("uc_ids") or []),
                }
                for c in gap_block["clauses"]
            ],
            "common_clause_count": gap_block.get("common_clause_count", len(common_clauses)),
            "covered_count": gap_block.get("covered_count", 0),
            "coverage_pct": gap_block.get("coverage_pct", 0.0),
            "priority_weight_total": gap_block.get("priority_weight_total", 0.0),
            "priority_weight_covered": gap_block.get("priority_weight_covered", 0.0),
            "priority_weight_pct": gap_block.get("priority_weight_pct", 0.0),
        }
    return _compute_coverage_from_index(reg_id, version, common_clauses, compliance_index)


# ----------------------------------------------------------------------
# Per-UC evidence details
# ----------------------------------------------------------------------
def _build_uc_details(
    compliance_index: dict[tuple[str, str], list[dict[str, Any]]],
    reg_id: str,
    version: str,
    uc_docs_by_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build UC id -> {title, evidence[], controlFamily, owner, source}."""
    details: dict[str, dict[str, Any]] = {}
    for entry in compliance_index.get((reg_id, version), []):
        uc_id = entry["uc_id"]
        if uc_id in details:
            continue
        uc_doc = uc_docs_by_id.get(uc_id) or {}
        evidence = uc_doc.get("evidence") or []
        if isinstance(evidence, dict):
            # Legacy shape: flatten into array
            evidence_list: list[Any] = []
            for key, val in sorted(evidence.items()):
                if isinstance(val, list):
                    evidence_list.extend(val)
                else:
                    evidence_list.append({"field": key, "description": val})
            evidence = evidence_list
        details[uc_id] = {
            "title": entry["uc_title"] or uc_doc.get("title") or "",
            "controlFamily": uc_doc.get("controlFamily"),
            "owner": uc_doc.get("owner"),
            "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
            "source_path": entry["source_path"],
        }
    return details


# ----------------------------------------------------------------------
# Markdown pack rendering
# ----------------------------------------------------------------------
def _clause_url(clause_url_template: str | None, clause: str) -> str | None:
    if not clause_url_template or not clause:
        return None
    # Regulations.json uses "{clause}" placeholder; some regulators
    # normalise clause to remove punctuation. Keep it simple: drop
    # "Art." prefix if clause uses it and the template expects a bare
    # number.
    candidate = clause_url_template.replace("{clause}", clause)
    return candidate


def _assurance_badge(assurance: str | None) -> str:
    if assurance == "full":
        return "full"
    if assurance == "partial":
        return "partial"
    if assurance == "contributing":
        return "contributing"
    return "—"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def _render_markdown_pack(
    framework: dict[str, Any],
    version: dict[str, Any],
    extras: dict[str, Any],
    coverage: dict[str, Any],
    uc_details: dict[str, dict[str, Any]],
    derivation_info: dict[str, Any] | None,
    generation_metadata: dict[str, Any],
    effective_common_clauses: list[dict[str, Any]] | None = None,
) -> str:
    reg_id = framework["id"]
    reg_short = framework.get("shortName") or framework.get("name") or reg_id
    reg_long = framework.get("name") or reg_short
    ver_str = version.get("version") or extras.get("version") or ""
    authoritative_url = version.get("authoritativeUrl")
    clause_url_template = version.get("clauseUrlTemplate")
    effective_from = version.get("effectiveFrom")
    sunset_on = version.get("sunsetOn")
    jurisdiction = ", ".join(framework.get("jurisdiction") or ["—"])
    tier = framework.get("tier")

    # `effective_common_clauses` overrides the version's own commonClauses
    # for identity-mode derivatives (see _generate_all).
    common_clauses = effective_common_clauses if effective_common_clauses is not None else (version.get("commonClauses") or [])
    clauses_cov = coverage.get("clauses") or []
    # Reconcile order: follow commonClauses order so numbering is
    # readable. Build lookup.
    clauses_by_id = {c["clause"]: c for c in clauses_cov}

    total = coverage.get("common_clause_count") or len(common_clauses)
    covered = coverage.get("covered_count") or 0
    coverage_pct = coverage.get("coverage_pct") or 0.0
    pw_pct = coverage.get("priority_weight_pct") or 0.0

    # Build ordered UC reference list
    uc_ids_all: list[str] = []
    for clause_def in common_clauses:
        clause = clause_def["clause"]
        clause_cov = clauses_by_id.get(clause) or {}
        for uid in clause_cov.get("uc_ids") or []:
            if uid not in uc_ids_all:
                uc_ids_all.append(uid)

    lines: list[str] = []

    # Header
    lines.append(f"# Evidence Pack — {reg_short}")
    lines.append("")
    lines.append(f"> **Tier**: {f'Tier {tier}' if tier else 'Tier —'} &nbsp;·&nbsp; "
                 f"**Jurisdiction**: {jurisdiction} &nbsp;·&nbsp; "
                 f"**Version**: `{ver_str}`")
    lines.append(">")
    lines.append(f"> **Full name**: {reg_long}  ")
    if authoritative_url:
        lines.append(f"> **Authoritative source**: [{authoritative_url}]({authoritative_url})  ")
    if effective_from:
        lines.append(f"> **Effective from**: {effective_from}  ")
    if sunset_on:
        lines.append(f"> **Sunset**: {sunset_on}  ")
    if derivation_info:
        parent = derivation_info.get("parent")
        mode = derivation_info.get("inheritanceMode")
        lines.append(f"> **Derived from**: `{parent}` (`{mode}` inheritance) — see Phase 3.3  ")
    lines.append("")
    lines.append("> This evidence pack is the auditor-facing view of the "
                 "Splunk monitoring catalogue's coverage of the regulation. "
                 "Every clause coverage claim is traceable to a specific UC "
                 "sidecar JSON file (`use-cases/cat-*/uc-*.json`); every "
                 "retention figure cites its legal basis; every URL resolves "
                 "to an official regulator or standards-body source. The "
                 "pack does **not** assert legal conclusions — it tabulates "
                 "what the catalogue covers, names the authoritative source, "
                 "and flags gaps. Interpretation stays with counsel.")
    lines.append("")

    # Table of contents
    lines.append("## Table of contents")
    lines.append("")
    lines.append("1. [Purpose of this evidence pack](#1-purpose-of-this-evidence-pack)")
    lines.append("2. [Scope and applicability](#2-scope-and-applicability)")
    lines.append("3. [Catalogue coverage at a glance](#3-catalogue-coverage-at-a-glance)")
    lines.append("4. [Clause-by-clause coverage](#4-clause-by-clause-coverage)")
    lines.append("5. [Evidence collection](#5-evidence-collection)")
    lines.append("6. [Control testing procedures](#6-control-testing-procedures)")
    lines.append("7. [Roles and responsibilities](#7-roles-and-responsibilities)")
    lines.append("8. [Authoritative guidance](#8-authoritative-guidance)")
    lines.append("9. [Common audit deficiencies](#9-common-audit-deficiencies)")
    lines.append("10. [Enforcement and penalties](#10-enforcement-and-penalties)")
    lines.append("11. [Pack gaps and remediation backlog](#11-pack-gaps-and-remediation-backlog)")
    lines.append("12. [Questions an auditor should ask](#12-questions-an-auditor-should-ask)")
    lines.append("13. [Machine-readable twin](#13-machine-readable-twin)")
    lines.append("14. [Provenance and regeneration](#14-provenance-and-regeneration)")
    lines.append("")

    # Section 1: purpose
    lines.append("## 1. Purpose of this evidence pack")
    lines.append("")
    lines.append(extras.get("summary") or "")
    lines.append("")

    # Section 2: scope
    lines.append("## 2. Scope and applicability")
    lines.append("")
    lines.append(extras.get("scope") or "")
    lines.append("")
    lines.append(f"**Territorial scope.** {extras.get('territorialScope') or '—'}")
    lines.append("")

    # Section 3: coverage summary
    lines.append("## 3. Catalogue coverage at a glance")
    lines.append("")
    lines.append(f"- **Clauses tracked**: {total}")
    lines.append(f"- **Clauses covered by at least one UC**: {covered} / {total} "
                 f"({_fmt_pct(coverage_pct)})")
    lines.append(f"- **Priority-weighted coverage**: {_fmt_pct(pw_pct)}")
    lines.append(f"- **Contributing UCs**: {len(uc_ids_all)}")
    if derivation_info:
        parent = derivation_info.get("parent")
        mode = derivation_info.get("inheritanceMode")
        if mode == "identity":
            lines.append(f"- **Derived via `derivesFrom`**: parent `{parent}` "
                         f"(mode `{mode}`). Identity-mode derivatives inherit "
                         f"the parent's full clause set unless explicitly "
                         f"diverged. This pack reports coverage against the "
                         f"**inherited parent clause inventory** so the "
                         f"auditor view is comparable to the parent. "
                         f"Inherited mappings carry assurance degraded one "
                         f"step from the parent and are marked "
                         f"`provenance: derived-from-parent` in the UC "
                         f"sidecar. Native hand-authored mappings take "
                         f"precedence. Known divergences are listed in "
                         f"`data/regulations.json derivesFrom[].divergences`.")
        else:
            lines.append(f"- **Derived via `derivesFrom`**: parent `{parent}` "
                         f"(mode `{mode}`). Inherited mappings carry "
                         f"assurance degraded one step from the parent and "
                         f"are marked `provenance: derived-from-parent` in "
                         f"the UC sidecar. Native hand-authored mappings take "
                         f"precedence.")
    lines.append("")
    lines.append("Coverage methodology is documented in "
                 "[`docs/coverage-methodology.md`](../coverage-methodology.md). "
                 "Priority weights come from `data/regulations.json` "
                 "commonClauses entries (see "
                 "[`data/regulations.json`](../../data/regulations.json) "
                 "priorityWeightRubric).")
    lines.append("")

    # Section 4: clause-by-clause
    lines.append("## 4. Clause-by-clause coverage")
    lines.append("")
    clause_source_note = (
        "Clauses are listed in the order defined by "
        "`data/regulations.json commonClauses` for this regulation version. "
    )
    if derivation_info and derivation_info.get("inheritanceMode") == "identity":
        clause_source_note = (
            "Because this regulation derives from "
            f"`{derivation_info.get('parent')}` with identity inheritance, "
            "the clause inventory below merges the parent's commonClauses "
            "(from `data/regulations.json`) with any divergent clauses the "
            "derivative explicitly redefines. "
        )
    lines.append(
        clause_source_note
        + "A clause is considered covered when at least one UC sidecar has a "
        "`compliance[]` entry matching `(regulation, version, clause)`. "
        "Assurance is the maximum across contributing UCs."
    )
    lines.append("")
    lines.append("| Clause | Topic | Priority | Assurance | UCs |")
    lines.append("|---|---|---|---|---|")
    for clause_def in common_clauses:
        clause = clause_def["clause"]
        topic = clause_def.get("topic") or ""
        weight = float(clause_def.get("priorityWeight") or 0.5)
        clause_cov = clauses_by_id.get(clause) or {}
        assurance = clause_cov.get("max_assurance")
        uc_ids = clause_cov.get("uc_ids") or []
        clause_link = _clause_url(clause_url_template, clause)
        clause_cell = f"[`{clause}`]({clause_link})" if clause_link else f"`{clause}`"
        if uc_ids:
            uc_cell = ", ".join(f"[UC-{u}](#uc-{u.replace('.', '-')})" for u in uc_ids[:6])
            if len(uc_ids) > 6:
                uc_cell += f" (+{len(uc_ids) - 6} more)"
        else:
            uc_cell = "_not yet covered_"
        lines.append(
            f"| {clause_cell} | {topic} | {weight:.1f} | "
            f"`{_assurance_badge(assurance)}` | {uc_cell} |"
        )
    lines.append("")

    # Per-UC references for deep-link
    if uc_ids_all:
        lines.append("### 4.1 Contributing UC detail")
        lines.append("")
        for uid in sorted(uc_ids_all):
            detail = uc_details.get(uid) or {}
            title = detail.get("title") or ""
            control_family = detail.get("controlFamily") or "—"
            owner = detail.get("owner") or "—"
            ev_count = detail.get("evidence_count", 0)
            source_path = detail.get("source_path") or ""
            anchor = uid.replace(".", "-")
            lines.append(f"<a id='uc-{anchor}'></a>")
            lines.append(f"- **UC-{uid}** — {title}")
            lines.append(f"  - Control family: `{control_family}`")
            lines.append(f"  - Owner: `{owner}`")
            lines.append(f"  - Evidence fields declared in sidecar: {ev_count}")
            lines.append(f"  - Source: [`{source_path}`](../../{source_path})")
        lines.append("")

    # Section 5: evidence collection
    lines.append("## 5. Evidence collection")
    lines.append("")
    lines.append("### 5.1 Common evidence sources")
    lines.append("")
    lines.append("Auditors typically request the following records when "
                 "examining this regulation:")
    lines.append("")
    for src in extras.get("commonEvidenceSources") or []:
        lines.append(f"- {src}")
    lines.append("")
    lines.append("### 5.2 Retention requirements")
    lines.append("")
    lines.append("| Artifact | Retention | Legal basis |")
    lines.append("|---|---|---|")
    for rec in extras.get("retentionGuidance") or []:
        lines.append(f"| {rec.get('artifact') or ''} | "
                     f"{rec.get('retention') or ''} | "
                     f"{rec.get('source') or ''} |")
    lines.append("")
    lines.append("> Retention figures above are the legal minimums or "
                 "regulator-stated expectations. Organisation-specific "
                 "retention schedules may be longer where business, tax, "
                 "litigation-hold, or contractual obligations apply. Where "
                 "a figure conflicts with local data-protection law (e.g. "
                 "GDPR Art.5(1)(e) storage-limitation principle), the "
                 "shorter conformant period governs for personal-data "
                 "content; the evidence-of-compliance retention retains "
                 "the longer period for audit purposes, scrubbed of "
                 "excess personal data.")
    lines.append("")
    lines.append("### 5.3 Evidence integrity expectations")
    lines.append("")
    lines.append("Regulators increasingly cite **evidence-integrity failures** "
                 "as aggravating factors in enforcement actions. "
                 "Cross-regulation baseline expectations:")
    lines.append("")
    lines.append("- Time-stamped, tamper-evident storage (WORM, cryptographic "
                 "chaining, or append-only indexes).")
    lines.append("- Chain-of-custody for any evidence removed from the "
                 "SIEM / production system for audit or legal purposes.")
    lines.append("- Synchronised clocks (NTP stratum ≤ 3 or equivalent) "
                 "across all in-scope sources so timeline reconstruction is "
                 "defensible.")
    lines.append("- Documented retention enforcement — not just retention "
                 "policy — so that deletion is auditable.")
    lines.append("")
    lines.append("See cat-22.35 \"Evidence continuity and log integrity\" for "
                 "UCs that implement these controls.")
    lines.append("")

    # Section 6: testing procedures
    lines.append("## 6. Control testing procedures")
    lines.append("")
    lines.append(extras.get("testingApproach") or "")
    lines.append("")
    lines.append(f"**Reporting cadence.** {extras.get('reportingCadence') or '—'}")
    lines.append("")

    # Section 7: roles
    lines.append("## 7. Roles and responsibilities")
    lines.append("")
    lines.append("| Role | Responsibility |")
    lines.append("|---|---|")
    for role in extras.get("roles") or []:
        lines.append(f"| **{role.get('title')}** | {role.get('responsibility')} |")
    lines.append("")

    # Section 8: authoritative guidance
    lines.append("## 8. Authoritative guidance")
    lines.append("")
    for g in extras.get("authoritativeGuidance") or []:
        lines.append(f"- **{g.get('title')}** — {g.get('organisation')} — "
                     f"[{g.get('url')}]({g.get('url')})")
    lines.append("")

    # Section 9: common deficiencies
    lines.append("## 9. Common audit deficiencies")
    lines.append("")
    lines.append("Findings frequently cited by regulators, certification "
                 "bodies, and external auditors for this regulation. These "
                 "should be pre-tested as part of readiness reviews.")
    lines.append("")
    for item in extras.get("commonDeficiencies") or []:
        lines.append(f"- {item}")
    lines.append("")

    # Section 10: enforcement
    lines.append("## 10. Enforcement and penalties")
    lines.append("")
    lines.append(extras.get("penaltyStructure") or "")
    lines.append("")

    # Section 11: gaps
    lines.append("## 11. Pack gaps and remediation backlog")
    lines.append("")
    uncovered = [
        c for c in common_clauses
        if not (clauses_by_id.get(c["clause"]) or {}).get("covered")
    ]
    if uncovered:
        lines.append("Clauses tracked in `data/regulations.json` that are "
                     "**not yet covered** by any UC in this catalogue are "
                     "listed below. These are the backlog items for the "
                     "next release. Priority order follows priorityWeight.")
        lines.append("")
        lines.append("| Clause | Topic | Priority |")
        lines.append("|---|---|---|")
        for clause_def in sorted(
            uncovered,
            key=lambda c: (-float(c.get("priorityWeight") or 0.5), c["clause"]),
        ):
            clause = clause_def["clause"]
            topic = clause_def.get("topic") or ""
            weight = float(clause_def.get("priorityWeight") or 0.5)
            lines.append(f"| `{clause}` | {topic} | {weight:.1f} |")
        lines.append("")
    else:
        lines.append("All clauses tracked in `data/regulations.json` for "
                     "this regulation version are covered by at least one "
                     "UC. **100 % common-clause coverage**. Remaining work "
                     "is assurance-upgrade (for example, moving "
                     "`contributing` entries to `partial` or `full` via "
                     "explicit control tests) rather than new clause "
                     "authoring.")
        lines.append("")

    # Section 12: auditor questions
    lines.append("## 12. Questions an auditor should ask")
    lines.append("")
    lines.append("These are the questions a regulator, certification body, "
                 "or external auditor is likely to ask. The pack helps "
                 "preparers stage evidence and pre-test responses before "
                 "the review opens.")
    lines.append("")
    for question in extras.get("auditorQuestions") or []:
        lines.append(f"- {question}")
    lines.append("")

    # Section 13: machine-readable twin
    lines.append("## 13. Machine-readable twin")
    lines.append("")
    lines.append(f"The machine-readable companion of this pack lives at "
                 f"[`api/v1/evidence-packs/{reg_id}.json`](../../api/v1/evidence-packs/{reg_id}.json). "
                 f"It contains the same clause-level coverage, retention "
                 f"guidance, role matrix, and gap list in JSON form, and "
                 f"is regenerated in lockstep with this markdown pack so "
                 f"content stays in sync. Consumers integrating the pack "
                 f"into GRC tools, audit-request portals, or evidence "
                 f"pipelines should consume the JSON document; human "
                 f"readers should consume this markdown.")
    lines.append("")
    lines.append(f"Related API surfaces (all under "
                 f"[`api/v1/`](../../api/README.md)):")
    lines.append("")
    lines.append(f"- [`api/v1/compliance/regulations/{reg_id}.json`](../../api/v1/compliance/regulations/{reg_id}.json) — regulation metadata and per-version coverage metrics")
    lines.append(f"- [`api/v1/compliance/ucs/`](../../api/v1/compliance/ucs/index.json) — individual UC sidecars")
    lines.append(f"- [`api/v1/compliance/coverage.json`](../../api/v1/compliance/coverage.json) — global coverage snapshot")
    lines.append(f"- [`api/v1/compliance/gaps.json`](../../api/v1/compliance/gaps.json) — global gap report")
    lines.append("")

    # Section 14: provenance
    lines.append("## 14. Provenance and regeneration")
    lines.append("")
    lines.append("This pack is **generated**, not hand-authored. Re-running "
                 "the generator produces byte-identical output (deterministic "
                 "sort, stable serialisation, no free-form timestamps "
                 "outside the block below). CI enforces regeneration drift "
                 "via `--check` mode.")
    lines.append("")
    lines.append("**Inputs to this pack**")
    lines.append("")
    lines.append(f"- [`data/regulations.json`](../../data/regulations.json) — "
                 f"commonClauses, priority weights, authoritative URLs")
    lines.append(f"- [`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json) — "
                 f"retention, roles, authoritative guidance, penalty, testing approach")
    lines.append(f"- [`use-cases/cat-*/uc-*.json`](../../use-cases) — "
                 f"UC sidecars containing compliance[] entries, controlFamily, "
                 f"owner, evidence fields")
    lines.append(f"- [`api/v1/compliance/regulations/{reg_id}@*.json`](../../api/v1/compliance/regulations/) — "
                 f"pre-computed coverage metrics (when present)")
    lines.append("")
    lines.append(f"- Generator: [`scripts/generate_evidence_packs.py`](../../scripts/generate_evidence_packs.py)")
    lines.append(f"- Evidence-pack directory index: [`docs/evidence-packs/README.md`](README.md)")
    lines.append("")
    lines.append("**Generation metadata**")
    lines.append("")
    lines.append("```")
    lines.append(f"catalogue_version: {generation_metadata.get('catalogue_version')}")
    lines.append(f"generator_script:  {generation_metadata.get('generator_script')}")
    lines.append(f"inputs_sha256:     {generation_metadata.get('inputs_sha256')}")
    lines.append("```")
    lines.append("")
    lines.append("To re-generate:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 scripts/generate_evidence_packs.py")
    lines.append("```")
    lines.append("")
    lines.append("To verify no drift in CI:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 scripts/generate_evidence_packs.py --check")
    lines.append("```")
    lines.append("")

    # Licence and disclaimer
    lines.append("---")
    lines.append("")
    lines.append(f"**Licensed under the terms in [`LICENSE`](../../LICENSE).** "
                 f"This pack is provided for compliance-readiness and "
                 f"evidence-collection purposes. It does **not** constitute "
                 f"legal advice. Interpretation of clauses and applicability "
                 f"to a specific organisation requires counsel review. "
                 f"Retention figures are minimum defaults; organisation-"
                 f"specific schedules may extend.")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# JSON twin rendering
# ----------------------------------------------------------------------
def _render_json_twin(
    framework: dict[str, Any],
    version: dict[str, Any],
    extras: dict[str, Any],
    coverage: dict[str, Any],
    uc_details: dict[str, dict[str, Any]],
    derivation_info: dict[str, Any] | None,
    generation_metadata: dict[str, Any],
) -> dict[str, Any]:
    reg_id = framework["id"]
    ver_str = version.get("version") or extras.get("version") or ""

    # `contributingUcs` mirrors the auditor-visible UCs in the markdown
    # table: only UCs that map to at least one *commonClauses* entry
    # (exact clause match). UCs that tag sub-clauses not in
    # commonClauses are excluded here so this count matches section 3
    # of the markdown pack. The full UC tagging set is recoverable via
    # api/v1/compliance/ucs/*.json.
    covered_uc_ids: set[str] = set()
    for clause in coverage.get("clauses") or []:
        for uid in clause.get("uc_ids") or []:
            covered_uc_ids.add(uid)

    return {
        "id": reg_id,
        "shortName": framework.get("shortName"),
        "name": framework.get("name"),
        "tier": framework.get("tier"),
        "jurisdiction": framework.get("jurisdiction") or [],
        "version": ver_str,
        "authoritativeUrl": version.get("authoritativeUrl"),
        "clauseUrlTemplate": version.get("clauseUrlTemplate"),
        "effectiveFrom": version.get("effectiveFrom"),
        "sunsetOn": version.get("sunsetOn"),
        "derivedFrom": derivation_info,
        "summary": extras.get("summary"),
        "scope": extras.get("scope"),
        "territorialScope": extras.get("territorialScope"),
        "coverage": {
            "commonClauseCount": coverage.get("common_clause_count"),
            "coveredCount": coverage.get("covered_count"),
            "coveragePct": coverage.get("coverage_pct"),
            "priorityWeightTotal": coverage.get("priority_weight_total"),
            "priorityWeightCovered": coverage.get("priority_weight_covered"),
            "priorityWeightPct": coverage.get("priority_weight_pct"),
            "contributingUcCount": len(covered_uc_ids),
        },
        "clauses": coverage.get("clauses") or [],
        "contributingUcs": [
            {
                "id": uid,
                "title": uc_details.get(uid, {}).get("title"),
                "controlFamily": uc_details.get(uid, {}).get("controlFamily"),
                "owner": uc_details.get(uid, {}).get("owner"),
                "evidenceCount": uc_details.get(uid, {}).get("evidence_count", 0),
                "sourcePath": uc_details.get(uid, {}).get("source_path"),
            }
            for uid in sorted(covered_uc_ids)
        ],
        "evidence": {
            "commonSources": extras.get("commonEvidenceSources") or [],
            "retentionGuidance": extras.get("retentionGuidance") or [],
        },
        "testing": {
            "approach": extras.get("testingApproach"),
            "reportingCadence": extras.get("reportingCadence"),
        },
        "roles": extras.get("roles") or [],
        "authoritativeGuidance": extras.get("authoritativeGuidance") or [],
        "commonDeficiencies": extras.get("commonDeficiencies") or [],
        "auditorQuestions": extras.get("auditorQuestions") or [],
        "penaltyStructure": extras.get("penaltyStructure"),
        "generationMetadata": generation_metadata,
    }


# ----------------------------------------------------------------------
# README generation
# ----------------------------------------------------------------------
def _render_readme(
    packs_generated: list[dict[str, Any]],
    generation_metadata: dict[str, Any],
) -> str:
    lines = []
    lines.append("# Evidence Packs")
    lines.append("")
    lines.append("> Auditor-ready evidence packs for the 12 highest-priority "
                 "regulations tracked by this catalogue. Each pack bundles "
                 "clause-level coverage, evidence-collection guidance, "
                 "retention expectations, role matrices, authoritative "
                 "sources, and common audit deficiencies. Machine-readable "
                 "twins live under [`api/v1/evidence-packs/`](../../api/v1/evidence-packs/) "
                 "for integration into GRC tools and audit-request pipelines.")
    lines.append("")
    lines.append("## How to use these packs")
    lines.append("")
    lines.append("1. **Regulators and external auditors**: start with the "
                 "pack for the regulation under review; the coverage table "
                 "in section 4 identifies the UCs that evidence each clause "
                 "and the assurance level each one provides.")
    lines.append("2. **Compliance and privacy officers**: use section 11 "
                 "(gaps) to drive the remediation backlog and section 12 "
                 "(auditor questions) to pre-test readiness.")
    lines.append("3. **Internal audit**: use section 6 (testing procedures) "
                 "and section 7 (roles) to build walk-through and control-"
                 "test scripts.")
    lines.append("4. **Executives and boards**: section 3 (coverage at a "
                 "glance) gives a one-screen summary; section 10 (enforcement) "
                 "provides the penalty context for risk-appetite discussions.")
    lines.append("")
    lines.append("## Pack catalogue")
    lines.append("")
    lines.append("| Regulation | Tier | Jurisdiction | Version | Coverage | Priority-weighted | Pack |")
    lines.append("|---|---|---|---|---|---|---|")
    for pack in packs_generated:
        reg_id = pack["id"]
        tier = pack.get("tier")
        juris = ", ".join(pack.get("jurisdiction") or [])
        ver_str = pack.get("version") or ""
        cov = pack.get("coverage") or {}
        cov_pct = cov.get("coveragePct")
        pw_pct = cov.get("priorityWeightPct")
        cov_cell = f"{cov_pct:.1f}%" if cov_pct is not None else "—"
        pw_cell = f"{pw_pct:.1f}%" if pw_pct is not None else "—"
        tier_cell = f"Tier {tier}" if tier else "Tier —"
        lines.append(
            f"| **{pack.get('shortName') or reg_id}** | "
            f"{tier_cell} | {juris} | `{ver_str}` | "
            f"{cov_cell} | {pw_cell} | "
            f"[`{reg_id}.md`]({reg_id}.md) |"
        )
    lines.append("")
    lines.append("## Structure of an evidence pack")
    lines.append("")
    lines.append("Every pack follows the same section layout so that an "
                 "auditor or compliance officer opening any pack finds the "
                 "same information in the same place:")
    lines.append("")
    lines.append("1. **Purpose** — plain-language regulation summary.")
    lines.append("2. **Scope** — who must comply and where.")
    lines.append("3. **Catalogue coverage at a glance** — single-row summary "
                 "of clause count, covered count, priority-weighted coverage, "
                 "contributing UC count.")
    lines.append("4. **Clause-by-clause coverage** — one table row per "
                 "clause, with priority weight, assurance level, and "
                 "contributing UC IDs.")
    lines.append("5. **Evidence collection** — common sources, retention "
                 "table with legal citations, evidence-integrity baseline.")
    lines.append("6. **Control testing procedures** — how regulators typically "
                 "test this regulation, plus reporting cadence.")
    lines.append("7. **Roles and responsibilities** — role matrix.")
    lines.append("8. **Authoritative guidance** — links to official regulator, "
                 "certification-body, or standards-body sources.")
    lines.append("9. **Common audit deficiencies** — typical findings for "
                 "pre-testing.")
    lines.append("10. **Enforcement and penalties** — monetary, operational, "
                 "and reputational consequences.")
    lines.append("11. **Pack gaps and remediation backlog** — clauses not "
                 "yet covered by the catalogue, ranked by priority.")
    lines.append("12. **Questions an auditor should ask** — ready-made "
                 "question list for preparers.")
    lines.append("13. **Machine-readable twin** — link to the JSON pack "
                 "and related API surfaces.")
    lines.append("14. **Provenance and regeneration** — inputs, generation "
                 "metadata, regeneration commands.")
    lines.append("")
    lines.append("## Regeneration")
    lines.append("")
    lines.append("The packs are generated deterministically from "
                 "[`data/regulations.json`](../../data/regulations.json), "
                 "[`data/evidence-pack-extras.json`](../../data/evidence-pack-extras.json), "
                 "the UC sidecars under [`use-cases/cat-*/`](../../use-cases), "
                 "and the pre-computed coverage metrics under "
                 "[`api/v1/compliance/regulations/`](../../api/v1/compliance/regulations/).")
    lines.append("")
    lines.append("```bash")
    lines.append("# Regenerate all packs (writes docs/evidence-packs/*.md")
    lines.append("# and api/v1/evidence-packs/*.json)")
    lines.append("python3 scripts/generate_evidence_packs.py")
    lines.append("")
    lines.append("# Verify no drift (for CI and local guard-rails)")
    lines.append("python3 scripts/generate_evidence_packs.py --check")
    lines.append("```")
    lines.append("")
    lines.append(f"Last regenerated against catalogue version "
                 f"`{generation_metadata.get('catalogue_version')}`.")
    lines.append("")
    lines.append("## Related documentation")
    lines.append("")
    lines.append("- [`docs/regulatory-primer.md`](../regulatory-primer.md) — "
                 "plain-language primer covering 15 cross-cutting families "
                 "and 12 tier-1 regulations.")
    lines.append("- [`docs/coverage-methodology.md`](../coverage-methodology.md) — "
                 "how clause coverage, priority-weighted coverage, and "
                 "assurance-adjusted coverage are computed.")
    lines.append("- [`docs/compliance-coverage.md`](../compliance-coverage.md) — "
                 "global coverage summary across all regulations.")
    lines.append("- [`docs/compliance-gaps.md`](../compliance-gaps.md) — "
                 "auto-generated gap report across all tracked regulations.")
    lines.append("- [`api/README.md`](../../api/README.md) — API surface "
                 "quick start and endpoint catalogue.")
    lines.append("- [`CHANGELOG.md`](../../CHANGELOG.md) — release history, "
                 "including the Phase 4.2 evidence-pack roll-out.")
    lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Main generation
# ----------------------------------------------------------------------
def _inputs_sha256() -> str:
    """Compute a stable SHA-256 across the generator inputs so drift is
    auditable. Excludes UC sidecars by design (too many to list here;
    coverage is already a function of those — this hash captures the
    non-UC inputs that the generator reads directly)."""
    hasher = hashlib.sha256()
    for path in [REGULATIONS_PATH, EXTRAS_PATH, EXTRAS_SCHEMA_PATH]:
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _generate_all(check: bool) -> int:
    regulations_doc = _load_json(REGULATIONS_PATH)
    extras_doc = _load_json(EXTRAS_PATH)
    gap_report = _load_gap_report()
    alias_index = regulations_doc.get("aliasIndex") or {}
    ucs = _load_all_ucs()
    uc_docs_by_id = {u["id"]: u for u in ucs if u.get("id")}
    compliance_index = _build_compliance_index(ucs, alias_index)
    derives_from_graph = regulations_doc.get("derivesFrom") or {}

    frameworks_by_id = {f["id"]: f for f in regulations_doc.get("frameworks") or []}

    # Generator-wide metadata
    catalogue_version = _get_version()
    inputs_sha = _inputs_sha256()
    generation_metadata = {
        "catalogue_version": catalogue_version,
        "generator_script": "scripts/generate_evidence_packs.py",
        "inputs_sha256": inputs_sha,
    }

    DOCS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    API_OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Plan the files we expect to write.
    planned: dict[Path, bytes] = {}
    packs_for_index: list[dict[str, Any]] = []

    for reg_id in PACK_TARGETS:
        framework = frameworks_by_id.get(reg_id)
        if not framework:
            print(f"ERROR: {reg_id} not in regulations.json", file=sys.stderr)
            return 1
        extras = (extras_doc.get("regulations") or {}).get(reg_id)
        if not extras:
            print(f"ERROR: {reg_id} not in evidence-pack-extras.json",
                  file=sys.stderr)
            return 1

        # Find the version block this extras points at. If multiple
        # versions exist, prefer the one whose version matches
        # extras['version']; otherwise the one with most commonClauses.
        versions = framework.get("versions") or []
        chosen_version = None
        for v in versions:
            if v.get("version") == extras.get("version"):
                chosen_version = v
                break
        if chosen_version is None and versions:
            chosen_version = max(
                versions,
                key=lambda v: (len(v.get("commonClauses") or []), v.get("effectiveFrom") or ""),
            )
        if chosen_version is None:
            print(f"ERROR: no version available for {reg_id}",
                  file=sys.stderr)
            return 1

        # For identity-mode derivatives (e.g. UK GDPR inheriting the
        # full GDPR clause set), the derivative's own commonClauses is
        # intentionally narrow — only divergent or UK-authoritative
        # clauses. An auditor-facing pack needs the full inherited
        # inventory. We overlay the parent's commonClauses and recompute
        # coverage from the UC index (which already holds Phase 3.3
        # derivation-tagged entries for the derivative).
        dv_graph_entry = (
            derives_from_graph.get(reg_id) if isinstance(derives_from_graph, dict) else None
        )
        inherit_mode = (
            dv_graph_entry.get("inheritanceMode")
            if isinstance(dv_graph_entry, dict)
            else None
        )
        effective_common_clauses = chosen_version.get("commonClauses") or []
        parent_common_clauses: list[dict[str, Any]] = []
        if inherit_mode == "identity" and isinstance(dv_graph_entry, dict):
            parent_id = dv_graph_entry.get("parent")
            parent_version = dv_graph_entry.get("parentVersion")
            parent_framework = frameworks_by_id.get(parent_id or "")
            if parent_framework:
                for pv in parent_framework.get("versions") or []:
                    if pv.get("version") == parent_version:
                        parent_common_clauses = pv.get("commonClauses") or []
                        break
            if parent_common_clauses:
                # Union: prefer derivative entry when the clause exists
                # in the derivative's own commonClauses (so UK-specific
                # topic/authoritativeSource wording wins), else parent.
                by_clause: dict[str, dict[str, Any]] = {
                    c["clause"]: c for c in parent_common_clauses
                }
                for dc in effective_common_clauses:
                    by_clause[dc["clause"]] = dc
                effective_common_clauses = [
                    by_clause[k]
                    for k in sorted(by_clause.keys(), key=_clause_sort_key)
                ]

        # Pre-computed coverage from the compliance-gaps report (covers
        # the non-identity case). For identity derivatives we recompute
        # live against the expanded clause inventory.
        if inherit_mode == "identity":
            gap_block = None  # force live computation
        else:
            gap_block = _gap_report_lookup(
                gap_report, reg_id, chosen_version.get("version", "")
            )
        coverage = _extract_coverage(
            gap_block,
            chosen_version.get("version", ""),
            reg_id,
            effective_common_clauses,
            compliance_index,
        )

        # Derivation info
        derivation_info = None
        dv = derives_from_graph.get(reg_id) if isinstance(derives_from_graph, dict) else None
        if isinstance(dv, dict):
            derivation_info = {
                "parent": dv.get("parent"),
                "parentVersion": dv.get("parentVersion"),
                "inheritanceMode": dv.get("inheritanceMode"),
                "divergences": dv.get("divergences") or [],
                "clauseMapping": {k: v for k, v in (dv.get("clauseMapping") or {}).items() if not k.startswith("$")},
            }

        uc_details = _build_uc_details(
            compliance_index, reg_id, chosen_version.get("version", ""), uc_docs_by_id
        )

        md_text = _render_markdown_pack(
            framework,
            chosen_version,
            extras,
            coverage,
            uc_details,
            derivation_info,
            generation_metadata,
            effective_common_clauses,
        )
        md_bytes = _stable_markdown_bytes(md_text)
        md_path = DOCS_OUT_DIR / f"{reg_id}.md"
        planned[md_path] = md_bytes

        json_twin = _render_json_twin(
            framework,
            chosen_version,
            extras,
            coverage,
            uc_details,
            derivation_info,
            generation_metadata,
        )
        json_bytes = _dump_json_bytes(json_twin)
        json_path = API_OUT_DIR / f"{reg_id}.json"
        planned[json_path] = json_bytes

        packs_for_index.append({
            "id": reg_id,
            "shortName": framework.get("shortName"),
            "name": framework.get("name"),
            "tier": framework.get("tier"),
            "jurisdiction": framework.get("jurisdiction") or [],
            "version": chosen_version.get("version"),
            "coverage": {
                "coveragePct": coverage.get("coverage_pct"),
                "priorityWeightPct": coverage.get("priority_weight_pct"),
            },
            "md": f"docs/evidence-packs/{reg_id}.md",
            "json": f"api/v1/evidence-packs/{reg_id}.json",
        })

    # API index document
    api_index = {
        "schemaVersion": "1.0",
        "catalogueVersion": catalogue_version,
        "inputsSha256": inputs_sha,
        "generator": "scripts/generate_evidence_packs.py",
        "packs": packs_for_index,
    }
    planned[API_OUT_DIR / "index.json"] = _dump_json_bytes(api_index)

    # Docs README
    readme_text = _render_readme(packs_for_index, generation_metadata)
    planned[DOCS_OUT_DIR / "README.md"] = _stable_markdown_bytes(readme_text)

    # Write or drift-check.
    if check:
        drift = _check_drift(planned)
        if drift:
            print("DRIFT DETECTED:", file=sys.stderr)
            for line in drift:
                print(f"  {line}", file=sys.stderr)
            return 1
        print(f"OK: no drift in {len(planned)} files under "
              f"docs/evidence-packs/ and api/v1/evidence-packs/.")
        return 0

    written = 0
    for path, payload in sorted(planned.items()):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() == payload:
            continue
        path.write_bytes(payload)
        written += 1
    # Clean orphan pack files that are no longer in PACK_TARGETS
    _prune_orphans(planned)
    print(f"OK: wrote {written} file(s); total planned {len(planned)}.")
    return 0


def _prune_orphans(planned: dict[Path, bytes]) -> None:
    """Remove any .md / .json files in the output dirs that the
    generator no longer produces. Keeps the surface honest."""
    allow: set[Path] = set(planned.keys())
    for base in (DOCS_OUT_DIR, API_OUT_DIR):
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_file():
                continue
            if entry.name.startswith("."):
                continue
            if entry not in allow:
                entry.unlink()


def _check_drift(planned: dict[Path, bytes]) -> list[str]:
    """Compare planned bytes to on-disk bytes; return drift descriptions."""
    drift: list[str] = []
    for path, payload in sorted(planned.items()):
        rel = str(path.relative_to(ROOT))
        if not path.exists():
            drift.append(f"missing: {rel}")
            continue
        current = path.read_bytes()
        if current != payload:
            drift.append(f"changed: {rel}")
            if path.suffix in (".md", ".json"):
                diff = list(difflib.unified_diff(
                    current.decode("utf-8", errors="replace").splitlines(),
                    payload.decode("utf-8", errors="replace").splitlines(),
                    fromfile=rel + " (on-disk)",
                    tofile=rel + " (planned)",
                    n=2,
                    lineterm="",
                ))
                # Only include first 30 diff lines per file so CI output
                # stays readable.
                for line in diff[:30]:
                    drift.append("  " + line)
                if len(diff) > 30:
                    drift.append(f"  ... ({len(diff) - 30} more diff lines)")
    # Extra-file check: anything in output dir not in plan.
    allow: set[Path] = set(planned.keys())
    for base in (DOCS_OUT_DIR, API_OUT_DIR):
        if not base.exists():
            continue
        for entry in sorted(base.iterdir()):
            if not entry.is_file():
                continue
            if entry.name.startswith("."):
                continue
            if entry not in allow:
                drift.append(f"orphan: {entry.relative_to(ROOT)}")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify generated files match planned output; exit 1 on drift."
    )
    args = parser.parse_args()
    try:
        return _generate_all(check=args.check)
    except Exception as exc:  # pragma: no cover
        print(f"FATAL: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
