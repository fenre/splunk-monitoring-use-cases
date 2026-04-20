#!/usr/bin/env python3
"""Phase 4 story-layer backfill migration.

One-shot migration that populates the three story-layer fields introduced
in ``uc.schema.json`` v1.6.0 / v1.6.1:

* ``controlObjective`` — one-sentence, UC-author-voice statement of what
  this UC accomplishes for this specific clause. Rendered as the headline
  of a (clause, UC) pair in ``compliance-story.html`` and in the
  clause-expansion rows of ``clause-navigator.html``.
* ``evidenceArtifact`` — the concrete, auditor-takeaway artefact produced
  when this UC is active and covering this clause. Rendered as the
  "acceptable evidence" column in ``clause-navigator.html``.
* ``requires_sme_review`` — boolean flag set to ``True`` when the two
  fields above were machine-generated (as they always are in this
  migration). Cleared by a SME signing off in
  ``data/provenance/sme-signoffs.json`` and then running this script
  again with ``--no-overwrite`` (which leaves vetted entries alone).

Behaviour
---------
Default run (no flags):
    * Walks every ``content/cat-*/UC-*.json`` sidecar.
    * For every ``compliance[]`` entry that is missing
      ``controlObjective`` or ``evidenceArtifact``:
        - Synthesises the two fields from the UC's own metadata
          (title / description / value / implementation / dataSources /
          spl) plus the clause metadata from ``data/regulations.json``.
        - Stamps ``requires_sme_review: true``.
    * Writes the sidecar back in canonical field order with a trailing
      newline so ``git diff`` stays legible.
    * Never touches an entry that already carries a non-empty
      ``controlObjective`` or ``evidenceArtifact`` (idempotent).

Also produces the obligation-text backfill manifest at
``data/per-regulation/phase4-obligation-backfill.md``. The script does
not invent regulator text (that requires legal review); it enumerates
every tier-1 ``commonClauses[]`` entry in ``data/regulations.json`` that
still lacks ``obligationText`` so SMEs can work through the list over
time.

Modes
-----
    python3 scripts/migrate_compliance_phase4.py
        Full run. Writes sidecars and the manifest.

    python3 scripts/migrate_compliance_phase4.py --check
        Drift-detect mode. Computes the diff without writing; exits
        non-zero if any file would change. Suitable for CI.

    python3 scripts/migrate_compliance_phase4.py --dry-run
        Like ``--check`` but exits 0; useful locally.

    python3 scripts/migrate_compliance_phase4.py --only UC-22.1.1
        Restrict the run to the listed UC(s). Space- or comma-separated;
        may be passed multiple times.

    python3 scripts/migrate_compliance_phase4.py --stats-only
        Print coverage statistics (how many entries have controlObjective
        / evidenceArtifact, how many still require SME review) without
        writing anything.

Idempotency & safety
--------------------
* ``--no-overwrite`` (default) skips any entry that already carries a
  non-empty ``controlObjective`` or ``evidenceArtifact``, preserving
  vetted text even after SMEs have cleared ``requires_sme_review``.
* ``--overwrite-auto`` re-generates text for entries where
  ``requires_sme_review`` is still ``true`` (machine-drafted,
  unreviewed) but leaves reviewed entries alone. Intended for re-runs
  after the generator improves.
* Hard-coded synthesis templates keep outputs deterministic across runs
  (same inputs always produce the same strings).

Security notes
--------------
* Only reads files under ``content/`` and ``data/`` relative to the repo
  root; no user-supplied paths are evaluated (codeguard-0-input-
  validation-injection, codeguard-0-file-handling-and-uploads).
* Path-confines every write with ``Path.resolve().is_relative_to()`` so
  a maliciously crafted ``--only`` cannot write outside the repo.
* No eval / no shell; only stdlib JSON parsing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"
PHASE4_MANIFEST = REPO_ROOT / "data" / "per-regulation" / "phase4-obligation-backfill.md"

# Canonical sidecar field order. Mirrors the Phase 3.1 generator so that
# repeated runs of all generators keep sidecars byte-comparable. Keep in
# sync with ``scripts/generate_phase3_1_backfill.py``.
SIDECAR_FIELD_ORDER: Tuple[str, ...] = (
    "$schema",
    "id",
    "title",
    "criticality",
    "difficulty",
    "monitoringType",
    "splunkPillar",
    "owner",
    "controlFamily",
    "exclusions",
    "evidence",
    "compliance",
    "controlTest",
    "dataSources",
    "app",
    "spl",
    "description",
    "value",
    "implementation",
    "visualization",
    "cimModels",
    "cimSpl",
    "references",
    "knownFalsePositives",
    "mitreAttack",
    "detectionType",
    "securityDomain",
    "requiredFields",
    "equipment",
    "equipmentModels",
    "status",
    "lastReviewed",
    "splunkVersions",
    "reviewer",
    "premiumApps",
    "attackTechnique",
    "grandmaExplanation",
    "detailedImplementation",
    "wave",
    "prerequisiteUseCases",
    "subcategory",
    "hardware",
    "telcoUseCase",
)

# Preferred field order within a compliance[] entry — keeps story-layer
# fields grouped together after the mapping identity and before
# provenance.
COMPLIANCE_ENTRY_ORDER: Tuple[str, ...] = (
    "regulation",
    "version",
    "clause",
    "clauseUrl",
    "mode",
    "assurance",
    "assurance_rationale",
    "controlObjective",
    "evidenceArtifact",
    "obligationRef",
    "requires_sme_review",
    "priorityWeight",
    "sourceTags",
    "provenance",
    "signedBy",
    "derivationSource",
)


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def _canonical_sidecar(sidecar: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in SIDECAR_FIELD_ORDER:
        if key in sidecar:
            ordered[key] = sidecar[key]
    for key, value in sidecar.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _canonical_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    ordered: Dict[str, Any] = {}
    for key in COMPLIANCE_ENTRY_ORDER:
        if key in entry:
            ordered[key] = entry[key]
    for key, value in entry.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


# ---------------------------------------------------------------------------
# Regulations index (clause metadata lookup)
# ---------------------------------------------------------------------------

class RegulationsIndex:
    """In-memory lookup for regulations.json metadata.

    Keys are the canonical ``{regulationId}@{version}#{clause}`` form
    used by ``obligationRef``. Aliases (alternative regulation names
    appearing on existing UCs) are resolved to the canonical regulation
    id via ``aliasIndex``.
    """

    def __init__(self, doc: Dict[str, Any]) -> None:
        self.doc = doc
        self.aliases = {
            k.lower(): v.lower() for k, v in doc.get("aliasIndex", {}).items()
        }
        self.by_id: Dict[str, Dict[str, Any]] = {}
        self.by_short: Dict[str, Dict[str, Any]] = {}
        for f in doc.get("frameworks", []):
            reg_id = f.get("id", "").lower()
            if reg_id:
                self.by_id[reg_id] = f
            short = (f.get("shortName") or "").lower()
            if short:
                self.by_short[short] = f

    def resolve_id(self, name: str) -> Optional[str]:
        """Return the canonical regulation id for any alias or short name."""
        if not name:
            return None
        key = str(name).strip().lower()
        if key in self.by_id:
            return key
        if key in self.by_short:
            return self.by_short[key].get("id", "").lower() or None
        if key in self.aliases:
            return self.aliases[key]
        # Fallback: strip common separators (e.g. "NIST 800-53" → "nist-800-53")
        normalised = re.sub(r"[\s/]+", "-", key).strip("-")
        if normalised in self.by_id:
            return normalised
        return None

    def clause_meta(
        self, reg_id: str, version: str, clause: str
    ) -> Optional[Dict[str, Any]]:
        """Return the commonClauses[] entry for the triple, if present."""
        framework = self.by_id.get(reg_id)
        if not framework:
            return None
        for v in framework.get("versions", []):
            if str(v.get("version")) == str(version):
                for cc in v.get("commonClauses", []):
                    if str(cc.get("clause")) == str(clause):
                        return cc
        return None

    def framework(self, reg_id: str) -> Optional[Dict[str, Any]]:
        return self.by_id.get(reg_id)


# ---------------------------------------------------------------------------
# Text synthesis
# ---------------------------------------------------------------------------

_MODE_OBJ_PREFIX = {
    "satisfies": "Evidence that",
    "detects-violation-of": "Detects violations of",
}

# Clamp helpers — the schema limits controlObjective to 20-280 chars and
# evidenceArtifact to 20-400 chars. Keep a margin.
_CO_MIN, _CO_MAX = 20, 280
_EA_MIN, _EA_MAX = 20, 400


def _first_sentence(text: str, fallback: str = "") -> str:
    if not text:
        return fallback
    # Take text up to first period / semicolon boundary.
    m = re.split(r"(?<=[.;])\s+", str(text).strip(), maxsplit=1)
    return (m[0] if m else str(text)).strip()


def _shorten(text: str, limit: int) -> str:
    t = " ".join(str(text).split())
    if len(t) <= limit:
        return t
    # Trim at the last word boundary within the limit and add an ellipsis.
    clip = t[: limit - 1]
    sp = clip.rfind(" ")
    if sp > 40:
        clip = clip[:sp]
    return clip.rstrip(" ,.;:") + "\u2026"


def _pad_to_min(text: str, minimum: int, tail: str) -> str:
    if len(text) >= minimum:
        return text
    padded = text.rstrip(".") + (tail if tail.startswith(".") else " " + tail)
    return padded


def _topic_phrase(clause_meta: Optional[Dict[str, Any]], clause: str) -> str:
    if clause_meta and clause_meta.get("topic"):
        return str(clause_meta["topic"]).strip()
    return clause or "this requirement"


def synthesise_control_objective(
    uc: Dict[str, Any],
    entry: Dict[str, Any],
    clause_meta: Optional[Dict[str, Any]],
) -> str:
    """One-sentence restatement of what the UC does for this clause.

    Template (satisfies mode):
        "Evidence that {regulation} {clause} ({topic}) is enforced \u2014
        Splunk UC {id}: {title}."
    Template (detects-violation-of mode):
        "Detects violations of {regulation} {clause} ({topic}) \u2014
        Splunk UC {id}: {title}."

    The ``({topic})`` qualifier is skipped when the topic is absent or
    identical to the clause code (avoids the redundant "PI1.3 (PI1.3)"
    we saw on initial drafts).

    UC titles are kept verbatim (preserving proper-noun casing such as
    "Modbus" or "GDPR PII Detection"). No gerund massaging is attempted
    because title phrases are noun-phrases, not verb-phrases, and
    forcing a gerund produced awkward sentences on the first draft.
    """
    mode = entry.get("mode", "satisfies")
    prefix = _MODE_OBJ_PREFIX.get(mode, "Contributes to")
    clause = entry.get("clause", "").strip()
    topic_raw = _topic_phrase(clause_meta, clause).strip()
    topic_is_redundant = (
        not topic_raw
        or topic_raw.lower() == clause.lower()
        or topic_raw.lower() == "this requirement"
    )
    topic_suffix = "" if topic_is_redundant else f" ({topic_raw})"

    reg = entry.get("regulation", "").strip() or "regulator"
    uc_id = str(uc.get("id") or "").strip()
    uc_id_disp = f"UC-{uc_id}" if uc_id and not uc_id.startswith("UC-") else uc_id
    title = str(uc.get("title") or "").strip()

    header = f"{prefix} {reg} {clause}{topic_suffix}"
    if mode == "satisfies":
        header = f"{header} is enforced"
    trailer = f"Splunk {uc_id_disp}: {title}" if title else f"Splunk {uc_id_disp}"
    sentence = f"{header} \u2014 {trailer}."

    sentence = _shorten(sentence, _CO_MAX)
    if len(sentence) < _CO_MIN:
        sentence = _pad_to_min(
            sentence, _CO_MIN,
            "Auto-drafted \u2014 SME review required.",
        )
    return sentence


_SOURCE_SUMMARY_LIMIT = 120


# Idiomatic placeholder strings that appear verbatim in ``dataSources``
# on many UCs but don't actually name a concrete source. These are
# rewritten to the generic phrasing used for missing sources so the
# resulting evidenceArtifact reads as a complete sentence.
_GENERIC_SOURCE_PLACEHOLDERS = {
    "see subcategory preamble",
    "see subcategory preamble.",
    "various",
    "n/a",
    "tbd",
}


def _summarise_sources(data_sources: Any) -> str:
    """Compact, auditor-friendly rendering of ``dataSources``.

    Long SPL-laden strings are replaced by a short noun phrase so the
    resulting evidenceArtifact reads cleanly (auditors care about the
    category of data, not the full sourcetype list). The first
    recognisable ``index=`` / ``sourcetype=`` token is surfaced when
    available so the artefact remains specific; otherwise we fall back
    to "catalogue-defined data sources" and defer the detail to the
    UC detail panel.

    Idiomatic placeholders such as "See subcategory preamble." are
    detected and rewritten to the generic phrasing so the artefact
    reads as a complete sentence rather than splicing the placeholder
    verbatim into "running on See subcategory preamble.".
    """
    if isinstance(data_sources, list):
        raw = "; ".join(str(s) for s in data_sources if s)
    else:
        raw = str(data_sources or "").strip()
    if not raw:
        return "catalogue-defined data sources"

    if raw.strip().lower() in _GENERIC_SOURCE_PLACEHOLDERS:
        return "catalogue-defined data sources (see UC detailedImplementation)"

    # Collapse internal whitespace / markdown backticks.
    clean = re.sub(r"\s+", " ", raw).replace("`", "")
    if len(clean) <= _SOURCE_SUMMARY_LIMIT:
        return clean

    # Try to surface a representative anchor (sourcetype/index/topic).
    anchor = None
    m = re.search(r"sourcetype\s*=\s*([\w:\"']+)", clean)
    if m:
        anchor = f"sourcetype {m.group(1).strip('\"')}"
    else:
        m = re.search(r"index\s*=\s*([\w:]+)", clean)
        if m:
            anchor = f"index {m.group(1)}"
        else:
            m = re.search(r"topic\s*=\s*([\w/]+)", clean)
            if m:
                anchor = f"MQTT topic {m.group(1)}"
    if anchor:
        return f"{anchor} and supporting catalogue-defined data sources"
    return "catalogue-defined data sources (see UC detailedImplementation)"


def synthesise_evidence_artifact(
    uc: Dict[str, Any],
    entry: Dict[str, Any],
) -> str:
    """Concrete artefact produced when the UC is active.

    Template:
        "Saved search '{UC-id}' running on {sources} and archived to
         the restricted audit_evidence index (default 7-year retention).
         Auto-drafted \u2014 SME review required."
    """
    uc_id = str(uc.get("id") or "").strip()
    uc_id_full = f"UC-{uc_id}" if uc_id and not uc_id.startswith("UC-") else uc_id
    sources = _summarise_sources(uc.get("dataSources"))
    sentence = (
        f"Saved search '{uc_id_full}' running on {sources}, archived to the "
        f"restricted audit_evidence index (default 7-year retention). "
        f"Auto-drafted \u2014 SME review required."
    )
    sentence = _shorten(sentence, _EA_MAX)
    if len(sentence) < _EA_MIN:
        sentence = _pad_to_min(
            sentence, _EA_MIN,
            "Auto-drafted \u2014 SME review required.",
        )
    return sentence


# ---------------------------------------------------------------------------
# obligationRef derivation
# ---------------------------------------------------------------------------

def derive_obligation_ref(
    entry: Dict[str, Any], index: RegulationsIndex
) -> Optional[str]:
    """Derive ``{regulationId}@{version}#{clause}`` if the entry resolves."""
    reg_name = entry.get("regulation")
    version = entry.get("version")
    clause = entry.get("clause")
    if not (reg_name and version and clause):
        return None
    reg_id = index.resolve_id(reg_name)
    if not reg_id:
        return None
    # Validate pattern (must match schema regex ^[a-z0-9-]+@[^#]+#.+$)
    ref = f"{reg_id}@{version}#{clause}"
    if not re.match(r"^[a-z0-9-]+@[^#]+#.+$", ref):
        return None
    return ref


# ---------------------------------------------------------------------------
# Compliance entry backfill
# ---------------------------------------------------------------------------

def _is_blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def backfill_entry(
    uc: Dict[str, Any],
    entry: Dict[str, Any],
    index: RegulationsIndex,
    overwrite_auto: bool,
) -> Tuple[Dict[str, Any], bool]:
    """Return a (possibly updated) entry and a changed-flag.

    Semantics:
      * Empty ``controlObjective`` / ``evidenceArtifact`` is always
        populated (and ``requires_sme_review: true`` is stamped).
      * Non-empty story fields are left alone unless
        ``overwrite_auto=True`` AND ``requires_sme_review`` is currently
        true (i.e. still flagged as machine-drafted).
      * ``obligationRef`` is derived when absent and the triple resolves;
        never overwritten once present.
    """
    new = dict(entry)
    changed = False

    # controlObjective
    co_current = new.get("controlObjective")
    auto_flag = bool(new.get("requires_sme_review"))
    should_write_co = _is_blank(co_current) or (overwrite_auto and auto_flag)
    if should_write_co:
        reg_id = index.resolve_id(new.get("regulation", ""))
        clause_meta = (
            index.clause_meta(reg_id, new.get("version", ""), new.get("clause", ""))
            if reg_id else None
        )
        new_co = synthesise_control_objective(uc, new, clause_meta)
        if new_co != co_current:
            new["controlObjective"] = new_co
            new["requires_sme_review"] = True
            changed = True

    # evidenceArtifact
    ea_current = new.get("evidenceArtifact")
    should_write_ea = _is_blank(ea_current) or (overwrite_auto and auto_flag)
    if should_write_ea:
        new_ea = synthesise_evidence_artifact(uc, new)
        if new_ea != ea_current:
            new["evidenceArtifact"] = new_ea
            new["requires_sme_review"] = True
            changed = True

    # obligationRef
    if _is_blank(new.get("obligationRef")):
        ref = derive_obligation_ref(new, index)
        if ref:
            new["obligationRef"] = ref
            changed = True

    return _canonical_entry(new), changed


# ---------------------------------------------------------------------------
# File walk
# ---------------------------------------------------------------------------

def iter_sidecars() -> List[Path]:
    return sorted(CONTENT_DIR.rglob("UC-*.json"))


def _ensure_inside_repo(path: Path) -> None:
    # Defensive: refuse to write outside the repo. ``Path.resolve()``
    # follows symlinks, closing the symlink-to-outside trick.
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(f"refusing to write outside repo: {path}") from exc


def process_sidecar(
    path: Path,
    index: RegulationsIndex,
    overwrite_auto: bool,
) -> Tuple[bool, Dict[str, int]]:
    """Backfill one sidecar. Returns (changed, stats)."""
    sidecar = _read_json(path)
    compliance = sidecar.get("compliance") or []
    if not isinstance(compliance, list):
        return False, {"entries": 0, "touched": 0}
    touched = 0
    new_compliance: List[Dict[str, Any]] = []
    for entry in compliance:
        if not isinstance(entry, dict):
            new_compliance.append(entry)
            continue
        new_entry, changed = backfill_entry(sidecar, entry, index, overwrite_auto)
        if changed:
            touched += 1
        new_compliance.append(new_entry)
    stats = {"entries": len(compliance), "touched": touched}
    if not touched:
        return False, stats
    sidecar["compliance"] = new_compliance
    sidecar = _canonical_sidecar(sidecar)
    # Double-check against the schema-imposed uniqueness rule — the
    # (regulation, version, clause) triple must be unique per UC.
    seen: set = set()
    for e in sidecar["compliance"]:
        key = (e.get("regulation"), e.get("version"), e.get("clause"))
        if key in seen:
            raise SystemExit(
                f"{path}: duplicate compliance triple {key} produced by migration"
            )
        seen.add(key)
    _ensure_inside_repo(path)
    return True, stats


# ---------------------------------------------------------------------------
# obligation-text backfill manifest
# ---------------------------------------------------------------------------

def build_obligation_manifest(index: RegulationsIndex) -> str:
    """Emit a markdown manifest of tier-1 clauses missing obligationText."""
    lines: List[str] = []
    lines.append("# Phase 4 obligation-text backfill manifest")
    lines.append("")
    lines.append(
        "Auto-generated by `scripts/migrate_compliance_phase4.py`. "
        "Rebuilds on every run; do not hand-edit."
    )
    lines.append("")
    lines.append(
        "Purpose: enumerates every tier-1 `commonClauses[]` entry in "
        "`data/regulations.json` that still lacks an authoritative "
        "`obligationText` + `obligationSource` pair. SMEs fill these in "
        "over time from the regulator-published source. Order is tier &rarr; "
        "regulation &rarr; version &rarr; clause; within each regulation the "
        "list is sorted by `priorityWeight` descending so the rows auditors "
        "care about most land at the top."
    )
    lines.append("")
    lines.append(
        "See [`docs/regulation-sources.md`](../../docs/regulation-sources.md) "
        "for authoritative URLs and the [obligation-text style guide]"
        "(../../docs/sme-review-guide.md#obligation-text) for writing rules "
        "(no paraphrasing; quote the regulator verbatim within the length "
        "budget)."
    )
    lines.append("")

    totals = {"done": 0, "missing": 0}
    per_tier_totals: Dict[int, Dict[str, int]] = {}

    for tier in (1, 2, 3):
        tier_rows: List[Tuple[str, str, str, Optional[float], str]] = []
        tier_done = tier_missing = 0
        for framework in index.doc.get("frameworks", []):
            if framework.get("tier") != tier:
                continue
            for version in framework.get("versions", []):
                common = version.get("commonClauses") or []
                # Sort within framework: priorityWeight desc, clause asc.
                common_sorted = sorted(
                    common,
                    key=lambda c: (
                        -(c.get("priorityWeight") or 0.0),
                        str(c.get("clause") or ""),
                    ),
                )
                for cc in common_sorted:
                    has_text = bool(cc.get("obligationText"))
                    if has_text:
                        tier_done += 1
                        totals["done"] += 1
                        continue
                    tier_missing += 1
                    totals["missing"] += 1
                    tier_rows.append(
                        (
                            framework.get("shortName")
                            or framework.get("id") or "?",
                            str(version.get("version") or "?"),
                            str(cc.get("clause") or "?"),
                            cc.get("priorityWeight"),
                            str(cc.get("topic") or "?"),
                        )
                    )
        per_tier_totals[tier] = {"done": tier_done, "missing": tier_missing}
        if not tier_rows and tier_done == 0:
            continue
        lines.append(f"## Tier {tier}")
        lines.append("")
        lines.append(
            f"`{tier_done}` done &middot; `{tier_missing}` still need authoritative "
            f"obligation text."
        )
        lines.append("")
        if tier_rows:
            lines.append("| Regulation | Version | Clause | Priority | Topic |")
            lines.append("| --- | --- | --- | --- | --- |")
            for reg, ver, clause, pw, topic in tier_rows:
                pw_str = f"{pw:.1f}" if isinstance(pw, (int, float)) else "—"
                lines.append(
                    f"| {reg} | `{ver}` | `{clause}` | {pw_str} | {topic} |"
                )
            lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"`{totals['done']}` clauses have authoritative text; "
        f"`{totals['missing']}` still need backfill."
    )
    lines.append("")
    for tier, c in sorted(per_tier_totals.items()):
        lines.append(
            f"* Tier {tier}: `{c['done']}` done, `{c['missing']}` pending."
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(
    *, check_only: bool, dry_run: bool, overwrite_auto: bool,
    only: Optional[List[str]] = None, stats_only: bool = False,
) -> int:
    if not REGULATIONS_PATH.exists():
        print(f"error: missing {REGULATIONS_PATH}", file=sys.stderr)
        return 2
    regs = _read_json(REGULATIONS_PATH)
    index = RegulationsIndex(regs)

    only_set = None
    if only:
        only_set = set()
        for token in only:
            for piece in re.split(r"[\s,]+", token.strip()):
                if not piece:
                    continue
                uid = piece.replace("UC-", "").strip()
                if uid:
                    only_set.add(uid)

    sidecars = iter_sidecars()
    if only_set:
        sidecars = [p for p in sidecars if p.stem.replace("UC-", "") in only_set]

    # ---- stats-only mode --------------------------------------------------
    if stats_only:
        total_entries = 0
        with_co = with_ea = with_both = still_review = 0
        for p in sidecars:
            try:
                d = _read_json(p)
            except Exception:
                continue
            for e in d.get("compliance") or []:
                if not isinstance(e, dict):
                    continue
                total_entries += 1
                has_co = not _is_blank(e.get("controlObjective"))
                has_ea = not _is_blank(e.get("evidenceArtifact"))
                if has_co:
                    with_co += 1
                if has_ea:
                    with_ea += 1
                if has_co and has_ea:
                    with_both += 1
                if e.get("requires_sme_review"):
                    still_review += 1
        print(f"compliance entries scanned: {total_entries}")
        print(f"  with controlObjective:   {with_co}")
        print(f"  with evidenceArtifact:   {with_ea}")
        print(f"  with both:               {with_both}")
        print(f"  still requires_sme_review=true: {still_review}")
        return 0

    # ---- full run ---------------------------------------------------------
    changed_paths: List[Path] = []
    touched_entries = 0
    for path in sidecars:
        try:
            changed, stats = process_sidecar(path, index, overwrite_auto)
        except Exception as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2
        if not changed:
            continue
        touched_entries += stats["touched"]
        changed_paths.append(path)
        if check_only or dry_run:
            continue
        sidecar = _canonical_sidecar(_read_json(path))
        # Re-run once to get the updated sidecar for writing.
        _, _ = process_sidecar(path, index, overwrite_auto)
        # process_sidecar only validated; actual write:
        _write_sidecar(path, index, overwrite_auto)

    # ---- obligation-text manifest ----------------------------------------
    manifest_text = build_obligation_manifest(index)
    manifest_changed = False
    if PHASE4_MANIFEST.exists():
        manifest_current = PHASE4_MANIFEST.read_text(encoding="utf-8")
        if manifest_current != manifest_text:
            manifest_changed = True
    else:
        manifest_changed = True
    if manifest_changed and not (check_only or dry_run):
        PHASE4_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        _ensure_inside_repo(PHASE4_MANIFEST)
        PHASE4_MANIFEST.write_text(manifest_text, encoding="utf-8")

    # ---- report -----------------------------------------------------------
    print(f"scanned sidecars: {len(sidecars)}")
    print(f"sidecars touched: {len(changed_paths)}")
    print(f"entries touched:  {touched_entries}")
    print(f"manifest changed: {manifest_changed}")

    if check_only and (changed_paths or manifest_changed):
        print(
            "\nFAIL: Phase 4 backfill drift detected. Run:\n"
            "    python3 scripts/migrate_compliance_phase4.py\n"
            "to regenerate the affected files.",
            file=sys.stderr,
        )
        return 1
    return 0


def _write_sidecar(path: Path, index: RegulationsIndex, overwrite_auto: bool) -> None:
    """Re-process the sidecar and write its canonical form back."""
    sidecar = _read_json(path)
    compliance = sidecar.get("compliance") or []
    if not isinstance(compliance, list):
        return
    new_compliance: List[Dict[str, Any]] = []
    for entry in compliance:
        if not isinstance(entry, dict):
            new_compliance.append(entry)
            continue
        new_entry, _ = backfill_entry(sidecar, entry, index, overwrite_auto)
        new_compliance.append(new_entry)
    sidecar["compliance"] = new_compliance
    _dump_json(path, _canonical_sidecar(sidecar))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill controlObjective / evidenceArtifact / "
                    "obligationRef on UC compliance[] entries (schema v1.6.1)."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Drift-detect mode. Exit 1 if any file would change.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute diff but do not write. Always exits 0.",
    )
    parser.add_argument(
        "--overwrite-auto", action="store_true",
        help="Re-generate story fields on entries still flagged "
             "requires_sme_review=true. Does NOT touch reviewed entries.",
    )
    parser.add_argument(
        "--only", action="append", default=[],
        help="Restrict to specific UC id(s). Space/comma-separated. "
             "May be repeated.",
    )
    parser.add_argument(
        "--stats-only", action="store_true",
        help="Print story-layer coverage stats and exit without writing.",
    )
    args = parser.parse_args(argv)

    return run(
        check_only=args.check,
        dry_run=args.dry_run,
        overwrite_auto=args.overwrite_auto,
        only=args.only,
        stats_only=args.stats_only,
    )


if __name__ == "__main__":
    sys.exit(main())
