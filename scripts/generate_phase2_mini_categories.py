#!/usr/bin/env python3
"""Phase 2.2 mini-category UC generator.

Consumes ``data/mini-categories/phase2.2.json`` (the authoring source of
truth) and:

1. Appends 35 new UCs (5 per mini-category, 22.35-22.49) to the cat-22
   markdown catalogue inside a ``<!-- PHASE-2.2 BEGIN -->`` / ``<!-- PHASE-2.2 END -->``
   fence so the render is idempotent.
2. Writes one JSON sidecar per new UC to ``use-cases/cat-22/uc-<id>.json``
   (same authoring shape as the Phase 1.6 exemplars).
3. Backfills the ``CIM Models:`` markdown field and the ``cimModels``
   sidecar field on the 40 Phase 1.6 exemplar UCs (22.35.1 .. 22.49.3)
   so the --full run of ``scripts/audit_uc_structure.py`` stays green.

All writes are deterministic: the same inputs produce byte-identical
outputs across machines. Pass ``--check`` to drift-detect in CI.

Security notes (codeguard-0-input-validation-injection,
codeguard-0-file-handling-and-uploads):
- All file writes are under repo-relative paths.
- No user input is evaluated; all UC data lives in the JSON source file.
- JSON is parsed with the stdlib (no external network, no schemas in
  flight at emission time — sidecars are validated by a separate audit).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
MD_SOURCE = REPO_ROOT / "use-cases" / "cat-22-regulatory-compliance.md"
SIDECAR_DIR = REPO_ROOT / "use-cases" / "cat-22"
DATA_FILE = REPO_ROOT / "data" / "mini-categories" / "phase2.2.json"

FENCE_BEGIN = "<!-- PHASE-2.2 BEGIN -->"
FENCE_END = "<!-- PHASE-2.2 END -->"
PHASE_1_6_END = "<!-- PHASE-1.6 END -->"

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

# Deterministic field order so sidecars round-trip byte-for-byte.
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
    # Keep any extra keys in a stable (sorted) order after the canonical set.
    for k in sorted(obj.keys()):
        if k not in ordered:
            ordered[k] = obj[k]
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

_RE_UC_HEAD = re.compile(r"^### UC-(22\.\d+\.\d+)\b", re.M)


def _render_markdown_block(uc: Dict) -> str:
    """Render a UC dict into the cat-22 markdown block format."""
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
    if uc.get("cimSpl"):
        lines.append("- **CIM SPL:**")
        lines.append("```spl")
        lines.append(uc["cimSpl"].rstrip())
        lines.append("```")
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
    return dict(sorted(grouped.items(), key=lambda kv: (int(kv[0].split(".")[0]),
                                                         int(kv[0].split(".")[1]))))


def _render_phase22_section(ucs: List[Dict], subcat_titles: Dict[str, str]) -> str:
    parts: List[str] = [
        FENCE_BEGIN,
        "",
        "<!--",
        "  The UC blocks between the PHASE-2.2 fences are generated from",
        "  data/mini-categories/phase2.2.json by",
        "  scripts/generate_phase2_mini_categories.py. Do not edit this",
        "  section by hand. Edit the JSON authoring source and re-run the",
        "  generator.",
        "-->",
        "",
    ]
    grouped = _group_by_subcat(ucs)
    for sub, subucs in grouped.items():
        title = subcat_titles.get(sub, "")
        parts.append(f"### {sub} — additional UCs ({title})")
        parts.append("")
        for uc in subucs:
            parts.append(_render_markdown_block(uc))
            parts.append("---")
            parts.append("")
    parts.append(FENCE_END)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CIM Models backfill on existing 40 exemplars
# ---------------------------------------------------------------------------

def _backfill_markdown_cim(md_text: str, cim_map: Dict[str, List[str]]) -> str:
    """Insert `- **CIM Models:** ...` right after the Visualization line of
    each UC listed in ``cim_map`` (if not already present). Idempotent."""

    def insert_for_block(block: str, uc_id: str) -> str:
        # Skip if CIM Models line already exists in this block.
        if re.search(r"^- \*\*CIM Models:\*\*", block, re.M):
            return block
        cim = ", ".join(cim_map[uc_id])
        cim_line = f"- **CIM Models:** {cim}"
        pattern = re.compile(r"(^- \*\*Visualization:\*\* [^\n]*\n)", re.M)
        if not pattern.search(block):
            # No Visualization line → append before the References line.
            ref_pat = re.compile(r"(^- \*\*References:\*\*)", re.M)
            if ref_pat.search(block):
                return ref_pat.sub(cim_line + "\n\\1", block, count=1)
            return block + "\n" + cim_line + "\n"
        return pattern.sub("\\1" + cim_line + "\n", block, count=1)

    starts = [(m.group(1), m.start()) for m in _RE_UC_HEAD.finditer(md_text)]
    if not starts:
        return md_text
    out_parts: List[str] = [md_text[: starts[0][1]]]
    for i, (uc_id, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(md_text)
        block = md_text[start:end]
        if uc_id in cim_map:
            block = insert_for_block(block, uc_id)
        out_parts.append(block)
    return "".join(out_parts)


def _backfill_sidecar_cim(sidecar_path: Path, cim_list: List[str], check: bool,
                          changed: List[Path]) -> None:
    if not sidecar_path.exists():
        return
    obj = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if obj.get("cimModels") == cim_list:
        return
    obj["cimModels"] = cim_list
    _write_text(sidecar_path, _dump_sidecar(obj), check, changed)


# ---------------------------------------------------------------------------
# Full-UC sidecar emission for the 35 new UCs
# ---------------------------------------------------------------------------

_DEFAULT_SIDECAR_KEYS = {
    "status": "draft",
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
    # version that disagrees with the committed tree.
    #
    # The carry-over is narrowly scoped to fields whose authoritative writer
    # lives elsewhere — native compliance[] stays owned by the manifest here.
    if existing_path is not None and existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

        # 1) derived-from-parent compliance entries from the Phase 3.3
        #    derivative-propagation generator. Native mappings always win on
        #    the (regulation, version, clause) tuple, so a derived entry is
        #    only appended when it doesn't collide. See
        #    docs/signed-provenance.md (§determinism) and
        #    scripts/generate_phase3_3_derivatives.py (§idempotence contract).
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
        #    equipment-tagging generator. These are not authored in this
        #    generator's manifest — scripts/generate_equipment_tags.py is
        #    their sole writer — but they ARE validated by
        #    schemas/uc.schema.json (and consumed by build.py / the API
        #    surface / the equipment-orphan lint). Carrying them over keeps
        #    this generator idempotent against a tree that has already been
        #    processed by the equipment generator.
        for k in ("equipment", "equipmentModels"):
            if k in existing and k not in side:
                side[k] = existing[k]

        # 3) lifecycle fields that Phase 5.2 / Phase E (SME sign-off program)
        #    owns.  This generator only seeds a sensible "draft" default at
        #    first-time UC creation; once a UC has been promoted to
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
    cim_map: Dict[str, List[str]] = data.get("cim_models_backfill", {})
    new_ucs: List[Dict] = data.get("new_ucs", [])
    subcat_titles: Dict[str, str] = data.get("subcat_titles", {})

    changed: List[Path] = []

    # --- 1. CIM Models backfill on existing 40 exemplar sidecars + markdown --
    md_text = _read_text(MD_SOURCE)
    new_md = _backfill_markdown_cim(md_text, cim_map)

    for uc_id, cim_list in cim_map.items():
        sidecar = SIDECAR_DIR / f"uc-{uc_id}.json"
        _backfill_sidecar_cim(sidecar, cim_list, args.check, changed)

    # --- 2. Emit sidecars for 35 new UCs ---------------------------------
    for uc in new_ucs:
        dest = SIDECAR_DIR / f"uc-{uc['id']}.json"
        side = _new_sidecar_from_uc(uc, existing_path=dest)
        _write_text(dest, _dump_sidecar(side), args.check, changed)

    # --- 3. Render + replace PHASE-2.2 markdown section ------------------
    # Section content (no surrounding newlines) — callers add them.
    section = _render_phase22_section(new_ucs, subcat_titles) if new_ucs else ""
    fence_re = re.compile(
        re.escape(FENCE_BEGIN) + r".*?" + re.escape(FENCE_END),
        re.S,
    )
    if fence_re.search(new_md):
        # Existing section → in-place byte-identical replacement.
        new_md = fence_re.sub(lambda _m: section, new_md, count=1) if section else \
            fence_re.sub("", new_md, count=1)
    elif section:
        # First-time insertion after the Phase-1.6 end marker.
        marker = PHASE_1_6_END
        if marker in new_md:
            new_md = new_md.replace(marker, marker + "\n\n" + section + "\n", 1)
        else:
            if not new_md.endswith("\n"):
                new_md += "\n"
            new_md += "\n" + section + "\n"

    _write_text(MD_SOURCE, new_md, args.check, changed)

    if args.check and changed:
        print("Phase 2.2 generator drift detected in:")
        for p in changed:
            print(f"  {p.relative_to(REPO_ROOT)}")
        return 1
    print(f"Phase 2.2 generator: {len(changed)} file(s) "
          f"{'would change' if args.check else 'written'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
