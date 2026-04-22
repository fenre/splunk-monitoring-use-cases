#!/usr/bin/env python3
"""Audit docs/regulatory-primer.md for stale counts, dead file refs, and jargon.

Compares machine-verifiable claims in the primer against the authoritative
sources (``content/cat-22-regulatory-compliance/_category.json`` and
``data/regulations.json``) and flags discrepancies.

Checks
------
1. **UC counts** — every numeric "ships N UCs" / table-row count in Section 4
   and Appendix A is compared against ``_category.json``.
2. **Framework totals** — "69-framework inventory", tier badge counts, and
   the T2/T3 framework tallies are compared against ``data/regulations.json``.
3. **File references** — every back-ticked ``data/...`` path mentioned in the
   primer is verified to exist on disk.
4. **Phase references** — any remaining "Phase N.N" tokens in the primer are
   flagged as internal jargon that should have been reworded.

Usage::

    python scripts/audit_regulatory_primer.py             # human report
    python scripts/audit_regulatory_primer.py --check     # non-zero exit on any HIGH finding
    python scripts/audit_regulatory_primer.py --strict    # HIGH + MED fail the exit code
    python scripts/audit_regulatory_primer.py --json      # JSON output
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIMER = os.path.join(REPO_ROOT, "docs", "regulatory-primer.md")
CATEGORY_JSON = os.path.join(
    REPO_ROOT, "content", "cat-22-regulatory-compliance", "_category.json"
)
REGULATIONS_JSON = os.path.join(REPO_ROOT, "data", "regulations.json")


@dataclass
class Finding:
    severity: str
    category: str
    message: str
    line: int = 0

    def human(self) -> str:
        loc = f" (line {self.line})" if self.line else ""
        return f"[{self.severity}] [{self.category}] {self.message}{loc}"


def _load_uc_counts() -> Dict[str, int]:
    """Return {subcategory_id: total_uc_count} aggregating extended subs."""
    with open(CATEGORY_JSON, encoding="utf-8") as f:
        cat = json.load(f)
    counts: Dict[str, int] = {}
    for sc in cat.get("subcategories", []):
        sid = str(sc.get("id", ""))
        uc = sc.get("useCaseCount", 0)
        m = re.match(r"^(\d+\.\d+)", sid)
        base_id = m.group(1) if m else sid
        counts[base_id] = counts.get(base_id, 0) + uc
    return counts


def _load_framework_tiers() -> Tuple[int, Dict[int, int]]:
    """Return (total_frameworks, {tier: count})."""
    with open(REGULATIONS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    fw = data["frameworks"]
    tiers: Dict[int, int] = {}
    for fobj in fw:
        t = fobj.get("tier", 0)
        tiers[t] = tiers.get(t, 0) + 1
    return len(fw), tiers


def _find_line(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def audit(primer_text: str) -> List[Finding]:
    findings: List[Finding] = []
    uc_counts = _load_uc_counts()
    total_fw, tier_counts = _load_framework_tiers()

    # --- UC count checks (body text + appendix table) ---
    # Body text: "ships N dedicated" / "ships N UCs" / "(N dedicated UCs)"
    # / "(N native UCs)" / "§22.X ships N UCs"
    body_pat = re.compile(
        r"§?22\.(\d+)\s+ships\s+(\d+)\s+"
        r"|"
        r"\((\d+)\s+(?:dedicated|native)\s+UCs?\)"
    )
    for m in body_pat.finditer(primer_text):
        if m.group(1) and m.group(2):
            sub_id = f"22.{m.group(1)}"
            claimed = int(m.group(2))
        elif m.group(3):
            ctx_start = max(0, m.start() - 200)
            ctx = primer_text[ctx_start : m.start()]
            sub_m = re.search(r"§22\.(\d+)", ctx)
            if not sub_m:
                continue
            sub_id = f"22.{sub_m.group(1)}"
            claimed = int(m.group(3))
        else:
            continue

        actual = uc_counts.get(sub_id)
        if actual is not None and claimed != actual:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="uc-count-body",
                    message=(
                        f"Body text claims {sub_id} has {claimed} UCs "
                        f"but _category.json says {actual}."
                    ),
                    line=_find_line(primer_text, m.start()),
                )
            )

    # Appendix A table rows: | 22.X | ... | N | ... |
    table_pat = re.compile(
        r"^\|\s*22\.(\d+)\s*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|",
        re.MULTILINE,
    )
    for m in table_pat.finditer(primer_text):
        sub_id = f"22.{m.group(1)}"
        claimed = int(m.group(2))
        actual = uc_counts.get(sub_id)
        if actual is not None and claimed != actual:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="uc-count-table",
                    message=(
                        f"Appendix A table claims {sub_id} has {claimed} UCs "
                        f"but _category.json says {actual}."
                    ),
                    line=_find_line(primer_text, m.start()),
                )
            )

    # --- Framework total checks ---
    fw_total_pat = re.compile(r"(\d+)-framework inventory")
    for m in fw_total_pat.finditer(primer_text):
        claimed = int(m.group(1))
        if claimed != total_fw:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="framework-total",
                    message=(
                        f"Primer claims {claimed}-framework inventory "
                        f"but regulations.json has {total_fw}."
                    ),
                    line=_find_line(primer_text, m.start()),
                )
            )

    # T2 intro count: "an additional N tier-2 frameworks"
    t2_intro = re.search(r"additional\s+(\d+)\s+tier-2", primer_text, re.IGNORECASE)
    if t2_intro:
        claimed = int(t2_intro.group(1))
        actual_t2 = tier_counts.get(2, 0)
        if claimed != actual_t2:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="tier2-count",
                    message=(
                        f"Primer claims {claimed} tier-2 frameworks "
                        f"but regulations.json has {actual_t2}."
                    ),
                    line=_find_line(primer_text, t2_intro.start()),
                )
            )

    # T2 badge line: "56 frameworks" in tier badge table
    t2_badge = re.search(
        r"\*\*Tier 2\*\*[^;]*;\s*(\d+)\s+frameworks", primer_text
    )
    if t2_badge:
        claimed = int(t2_badge.group(1))
        actual_t2 = tier_counts.get(2, 0)
        if claimed != actual_t2:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="tier2-badge",
                    message=(
                        f"T2 badge claims {claimed} frameworks "
                        f"but regulations.json has {actual_t2}."
                    ),
                    line=_find_line(primer_text, t2_badge.start()),
                )
            )

    # T3 badge: "N today"
    t3_badge = re.search(
        r"\*\*Tier 3\*\*[^;]*;\s*(\d+)\s+today", primer_text
    )
    if t3_badge:
        claimed = int(t3_badge.group(1))
        actual_t3 = tier_counts.get(3, 0)
        if claimed != actual_t3:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="tier3-badge",
                    message=(
                        f"T3 badge claims {claimed} today "
                        f"but regulations.json has {actual_t3}."
                    ),
                    line=_find_line(primer_text, t3_badge.start()),
                )
            )

    # --- File reference checks ---
    file_ref_pat = re.compile(r"`(data/[^`]+)`")
    for m in file_ref_pat.finditer(primer_text):
        ref_path = m.group(1)
        # Skip glob-style references (e.g. data/crosswalks/*)
        if "*" in ref_path or "{" in ref_path:
            continue
        full = os.path.join(REPO_ROOT, ref_path)
        if not os.path.exists(full):
            findings.append(
                Finding(
                    severity="HIGH",
                    category="dead-file-ref",
                    message=f"File reference `{ref_path}` does not exist on disk.",
                    line=_find_line(primer_text, m.start()),
                )
            )

    # --- Phase reference checks ---
    phase_pat = re.compile(r"\bPhase\s+\d+\.\d+\b")
    for m in phase_pat.finditer(primer_text):
        findings.append(
            Finding(
                severity="MED",
                category="phase-jargon",
                message=(
                    f"Internal jargon \"{m.group(0)}\" found — "
                    f"reword to a functional description."
                ),
                line=_find_line(primer_text, m.start()),
            )
        )

    return findings


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Exit 1 on any HIGH finding")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any HIGH or MED finding",
    )
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args(argv)

    with open(PRIMER, encoding="utf-8") as f:
        primer_text = f.read()

    all_findings = audit(primer_text)

    if args.json:
        print(json.dumps([asdict(f) for f in all_findings], indent=2))
    else:
        print("=" * 72)
        print("Regulatory primer freshness audit")
        print("=" * 72)
        counts: dict[str, int] = {}
        for f in all_findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        print(
            "Findings: "
            + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            if counts
            else "Findings: 0"
        )
        print()
        if all_findings:
            for f in all_findings:
                print(f.human())
        else:
            print("All primer claims match the authoritative sources.")

    if args.strict:
        severity_order = {"HIGH": 3, "MED": 2, "LOW": 1}
        n_fail = sum(1 for f in all_findings if severity_order.get(f.severity, 0) >= 2)
        return 1 if n_fail > 0 else 0
    if args.check:
        n_high = sum(1 for f in all_findings if f.severity == "HIGH")
        return 1 if n_high > 0 else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
