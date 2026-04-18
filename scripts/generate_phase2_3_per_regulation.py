#!/usr/bin/env python3
"""Phase 2.3 per-regulation content-fill UC generator.

Consumes ``data/per-regulation/phase2.3.json`` (the authoring source of
truth for Phase 2.3 — the per-regulation content fills that close the
remaining clause gaps for the thinnest tier-1 frameworks: DORA,
ISO/IEC 27001:2022, SOC 2 2017 TSC, PCI-DSS v4.0 and SOX-ITGC (PCAOB
AS 2201)) and:

1. Appends 45 new UCs to the cat-22 markdown catalogue inside a
   ``<!-- PHASE-2.3 BEGIN -->`` / ``<!-- PHASE-2.3 END -->`` fence so
   the render is idempotent and the generator can be re-run at any
   time without clobbering hand-authored content.
2. Writes one JSON sidecar per new UC to ``use-cases/cat-22/uc-<id>.json``
   (same authoring shape as the Phase 1.6 exemplars and the Phase 2.2
   mini-category UCs).

All writes are deterministic: the same inputs produce byte-identical
outputs across machines. Pass ``--check`` to drift-detect in CI — the
generator exits non-zero if any tracked file would change on disk.

Security notes (codeguard-0-input-validation-injection,
codeguard-0-file-handling-and-uploads):
- All file writes are under repo-relative paths. No user input is
  evaluated; all UC data lives in the JSON authoring source file.
- JSON is parsed with the stdlib (no external network, no schema
  resolution in flight at emission time — sidecars are validated by
  ``scripts/audit_compliance_mappings.py`` and
  ``scripts/audit_uc_structure.py``).
- SPL text is emitted verbatim from the authoring source; Splunk
  Cloud compat + hallucination audits run in a separate CI step.

Design notes:
- This generator MIRRORS the shape of
  ``scripts/generate_phase2_mini_categories.py`` on purpose — two
  generators that share the same authoring conventions and sidecar
  field order are cheaper to maintain than one clever script.
- The fence lives AFTER the Phase 2.2 fence in the markdown so that
  per-regulation content fills render underneath the cross-regulation
  mini-categories, preserving reader flow.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_SOURCE = REPO_ROOT / "use-cases" / "cat-22-regulatory-compliance.md"
SIDECAR_DIR = REPO_ROOT / "use-cases" / "cat-22"
DATA_FILE = REPO_ROOT / "data" / "per-regulation" / "phase2.3.json"

FENCE_BEGIN = "<!-- PHASE-2.3 BEGIN -->"
FENCE_END = "<!-- PHASE-2.3 END -->"
PHASE_22_END = "<!-- PHASE-2.2 END -->"
PHASE_16_END = "<!-- PHASE-1.6 END -->"

CRITICALITY_EMOJI = {
    "critical": "🔴 Critical",
    "high": "🟠 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}
DIFFICULTY_EMOJI = {
    "beginner": "🟢 Beginner",
    "intermediate": "🔵 Intermediate",
    "advanced": "🟠 Advanced",
    "expert": "🔴 Expert",
}

# Deterministic field order for sidecars; mirrors the Phase 2.2 generator
# so the two outputs are byte-comparable. See SIDECAR_FIELD_ORDER in
# scripts/generate_phase2_mini_categories.py.
SIDECAR_FIELD_ORDER = [
    "$schema", "id", "title",
    "criticality", "difficulty", "monitoringType",
    "splunkPillar", "owner", "controlFamily",
    "exclusions", "evidence",
    "compliance", "controlTest",
    "dataSources", "app",
    "spl", "description", "value", "implementation", "visualization",
    "cimModels",
    "references",
    "knownFalsePositives",
    "mitreAttack",
    "detectionType", "securityDomain", "requiredFields",
    "equipment", "equipmentModels",
    "status", "lastReviewed", "splunkVersions", "reviewer",
]


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str, check: bool, changed: List[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == text:
        return
    changed.append(path)
    if not check:
        path.write_text(text, encoding="utf-8")


def _dump_sidecar(obj: Dict) -> str:
    ordered = {k: obj[k] for k in SIDECAR_FIELD_ORDER if k in obj}
    for k in sorted(obj.keys()):
        if k not in ordered:
            ordered[k] = obj[k]
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_markdown_block(uc: Dict) -> str:
    """Render a UC dict into the cat-22 markdown block format.

    Mirrors Phase 2.2's ``_render_markdown_block`` exactly so the
    render is visually identical between the two phases.
    """
    lines: List[str] = []
    lines.append(f"### UC-{uc['id']} · {uc['title']}")
    lines.append(f"- **Criticality:** {CRITICALITY_EMOJI[uc['criticality']]}")
    lines.append(f"- **Difficulty:** {DIFFICULTY_EMOJI[uc['difficulty']]}")
    lines.append(f"- **Monitoring type:** {', '.join(uc['monitoringType'])}")
    if uc.get("mitreAttack"):
        lines.append(f"- **MITRE ATT&CK:** {', '.join(uc['mitreAttack'])}")
    lines.append(f"- **Splunk Pillar:** {uc['splunkPillar']}")
    regs = sorted({c["regulation"] for c in uc.get("compliance", [])})
    if regs:
        lines.append(f"- **Regulations:** {', '.join(regs)}")
    lines.append(f"- **Value:** {uc['value']}")
    lines.append(f"- **App/TA:** {uc['app']}")
    lines.append(f"- **Data Sources:** {uc['dataSources']}")
    lines.append("- **SPL:**")
    lines.append("```spl")
    lines.append(uc["spl"].rstrip())
    lines.append("```")
    lines.append(f"- **Implementation:** {uc['implementation']}")
    lines.append(f"- **Visualization:** {uc['visualization']}")
    lines.append(f"- **CIM Models:** {', '.join(uc.get('cimModels', ['N/A']))}")
    lines.append(f"- **Known false positives:** {uc['knownFalsePositives']}")
    ref_md = ", ".join(f"[{r['title']}]({r['url']})" for r in uc.get("references", []))
    lines.append(f"- **References:** {ref_md}")
    return "\n".join(lines) + "\n"


def _group_by_subcat(ucs: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for uc in ucs:
        sub = ".".join(uc["id"].split(".")[:2])
        grouped.setdefault(sub, []).append(uc)
    for sub in grouped:
        grouped[sub].sort(key=lambda x: int(x["id"].split(".")[-1]))
    # Numeric sort by (major, minor) so 22.3 precedes 22.11.
    return dict(sorted(grouped.items(), key=lambda kv: (int(kv[0].split(".")[0]),
                                                         int(kv[0].split(".")[1]))))


def _render_phase23_section(ucs: List[Dict], subcat_titles: Dict[str, str]) -> str:
    parts: List[str] = [
        FENCE_BEGIN,
        "",
        "<!--",
        "  The UC blocks between the PHASE-2.3 fences are generated from",
        "  data/per-regulation/phase2.3.json by",
        "  scripts/generate_phase2_3_per_regulation.py. Do not edit this",
        "  section by hand. Edit the JSON authoring source and re-run the",
        "  generator. These UCs are per-regulation content fills that close",
        "  the remaining clause gaps for the thinnest tier-1 frameworks.",
        "-->",
        "",
    ]
    grouped = _group_by_subcat(ucs)
    for sub, subucs in grouped.items():
        title = subcat_titles.get(sub, "")
        parts.append(f"### {sub} — {title} (extended clauses)")
        parts.append("")
        for uc in subucs:
            parts.append(_render_markdown_block(uc))
            parts.append("---")
            parts.append("")
    parts.append(FENCE_END)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Sidecar emission
# ---------------------------------------------------------------------------

_DEFAULT_SIDECAR_KEYS = {
    # Phase 2.3 UCs are fully authored (SPL + compliance[] + controlTest[] +
    # references) and pass the compliance-mapping, structure and SPL
    # hallucination audits; they are awaiting SME sign-off (that happens in
    # Phase 5.2). "community" is the exact schema term for that lifecycle
    # stage ("contributed, unreviewed") and carries a 1.0 multiplier in
    # docs/coverage-methodology.md, so these UCs flip their tagged tier-1
    # clauses from GAP to COVERED in reports/compliance-gaps.json — which
    # is the explicit Phase 2.3 acceptance criterion.
    "status": "community",
    "lastReviewed": "2026-04-16",
    "splunkVersions": ["9.2+", "Cloud"],
    "reviewer": "N/A",
}


def _new_sidecar_from_uc(uc: Dict, existing_path: Path | None = None) -> Dict:
    side: Dict = {"$schema": "../../schemas/uc.schema.json"}
    side.update(uc)
    for k, v in _DEFAULT_SIDECAR_KEYS.items():
        side.setdefault(k, v)

    # Preserve fields that are authored by downstream generators, not by this
    # one. Without this carry-over the --check drift guard would fail
    # immediately after any downstream generator ran: this generator would
    # regenerate the sidecar from its manifest and produce a stripped-down
    # version that disagrees with the committed tree. See
    # scripts/generate_phase2_mini_categories.py for the matching merge logic
    # in the Phase 2.2 sibling generator.
    if existing_path is not None and existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

        # 1) derived-from-parent compliance entries that Phase 3.3 appends.
        #    Native mappings always win on the (regulation, version, clause)
        #    tuple, so a derived entry is only appended when it doesn't
        #    collide. See scripts/generate_phase3_3_derivatives.py for the
        #    idempotence contract.
        derived_carry_over: List[Dict] = [
            e for e in existing.get("compliance", []) or []
            if isinstance(e, dict) and e.get("provenance") == "derived-from-parent"
        ]
        if derived_carry_over:
            current = list(side.get("compliance", []) or [])
            native_keys = {
                (c.get("regulation"), c.get("version"), c.get("clause"))
                for c in current
                if isinstance(c, dict)
            }
            for entry in derived_carry_over:
                key = (entry.get("regulation"), entry.get("version"), entry.get("clause"))
                if key in native_keys:
                    continue
                current.append(entry)
                native_keys.add(key)
            side["compliance"] = current

        # 2) equipment[] and equipmentModels[] from the Phase 5.5 structured
        #    equipment-tagging generator. scripts/generate_equipment_tags.py
        #    is their sole writer — this generator only preserves them so the
        #    --check guard stays green after a post-hoc equipment regen.
        for k in ("equipment", "equipmentModels"):
            if k in existing and k not in side:
                side[k] = existing[k]

        # 3) lifecycle fields that Phase 5.2 / Phase E (SME sign-off program)
        #    owns.  This generator only seeds a sensible "community" default
        #    at first-time UC creation; once a UC has been promoted to
        #    ``verified`` by scripts/archive/generate_phase_e_signoffs.py (with a
        #    matching sme-signoffs.json record), or hand-edited by a
        #    reviewer, we must not clobber it on regeneration.  Any existing
        #    value always wins — the generator is never the authority on
        #    lifecycle.
        for k in ("status", "lastReviewed", "reviewer"):
            if k in existing:
                side[k] = existing[k]
    return side


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="Do not write any files; exit 1 on drift.")
    args = ap.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    new_ucs: List[Dict] = data.get("new_ucs", [])
    subcat_titles: Dict[str, str] = data.get("subcat_titles", {})

    changed: List[Path] = []

    # --- 1. Emit sidecars for the 45 new UCs ------------------------------
    for uc in new_ucs:
        dest = SIDECAR_DIR / f"uc-{uc['id']}.json"
        side = _new_sidecar_from_uc(uc, existing_path=dest)
        _write_text(dest, _dump_sidecar(side), args.check, changed)

    # --- 2. Render + replace PHASE-2.3 markdown section -------------------
    md_text = _read_text(MD_SOURCE)
    section = _render_phase23_section(new_ucs, subcat_titles) if new_ucs else ""
    fence_re = re.compile(
        re.escape(FENCE_BEGIN) + r".*?" + re.escape(FENCE_END),
        re.S,
    )
    if fence_re.search(md_text):
        new_md = (fence_re.sub(lambda _m: section, md_text, count=1)
                  if section else fence_re.sub("", md_text, count=1))
    elif section:
        # First-time insertion: prefer after PHASE-2.2 end marker, then
        # PHASE-1.6 end marker, then end of file.
        anchor = None
        if PHASE_22_END in md_text:
            anchor = PHASE_22_END
        elif PHASE_16_END in md_text:
            anchor = PHASE_16_END
        if anchor:
            new_md = md_text.replace(anchor, anchor + "\n\n" + section + "\n", 1)
        else:
            new_md = md_text
            if not new_md.endswith("\n"):
                new_md += "\n"
            new_md += "\n" + section + "\n"
    else:
        new_md = md_text

    _write_text(MD_SOURCE, new_md, args.check, changed)

    if args.check and changed:
        print("Phase 2.3 generator drift detected in:")
        for p in changed:
            print(f"  {p.relative_to(REPO_ROOT)}")
        return 1
    print(f"Phase 2.3 generator: {len(changed)} file(s) "
          f"{'would change' if args.check else 'written'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
