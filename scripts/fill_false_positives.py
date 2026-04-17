#!/usr/bin/env python3
"""Fill the `- **Known false positives:**` line for every security-relevant UC
that is missing one.

Security-relevant = categories 9 (IAM), 10 (Security), 14 (OT/IoT), 17 (Zero
Trust), 22 (Compliance).

Rather than inventing detection-specific details (which would be hallucination)
the script picks from a small set of honest archetypes keyed on the UC's
Detection type or Monitoring type. Each archetype is phrased as guidance for
the analyst and can be refined per-UC by a reviewer later.

Usage:
    python3 scripts/fill_false_positives.py          # dry run
    python3 scripts/fill_false_positives.py --write  # persist
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
UC_DIR = os.path.join(REPO_ROOT, "use-cases")

SECURITY_CATS = {"09", "10", "14", "17", "22"}

ARCHETYPES = {
    "TTP": (
        "Legitimate use of dual-purpose administrative tools (e.g. PowerShell, "
        "SSH, cloud CLIs) during maintenance or deployment can match this "
        "pattern — correlate with change tickets, asset criticality and user "
        "role before escalating."
    ),
    "Anomaly": (
        "Seasonal traffic, marketing campaigns, backups or project rollouts "
        "can shift the baseline — tune per-entity baselines and widen the "
        "training window if the signal becomes noisy."
    ),
    "Hunting": (
        "Broad scope: expect noise. Triage using asset criticality, user "
        "role and recent change-management activity; promote to a detection "
        "only after stable tuning."
    ),
    "Baseline": (
        "Planned growth, business cycles, or product launches may legitimately "
        "exceed the baseline — correlate with capacity plans and change windows."
    ),
    "Correlation": (
        "Missing or delayed events from any joined source (CMDB, identity, "
        "vulnerability feed) can produce spurious matches — monitor lookup "
        "freshness and joined-source lag."
    ),
    "Operational metrics": (
        "Planned maintenance, backups, or batch jobs can drive metrics "
        "outside normal bands — correlate with change management windows."
    ),
    "default": (
        "Administrative tasks, scheduled jobs or platform updates can match "
        "this pattern — correlate with change management, maintenance windows "
        "and user role before raising severity."
    ),
}

UC_HEAD_RE = re.compile(r"^### UC-(\d+)\.(\d+)\.(\d+)\s+·\s+", re.MULTILINE)
ANY_HEADING_RE = re.compile(r"^#{1,3}\s+", re.MULTILINE)
REF_LINE_RE = re.compile(r"^- \*\*References:\*\*[^\n]*$", re.MULTILINE)
STATUS_LINE_RE = re.compile(r"^- \*\*(?:Status|Last reviewed|Splunk versions|Reviewer):\*\*", re.MULTILINE)
SEP_RE = re.compile(r"^---\s*$", re.MULTILINE)


def split_ucs(text: str) -> List[Tuple[int, int, str]]:
    """Return [(start, end, uc_id)] for each UC block."""
    heads = list(UC_HEAD_RE.finditer(text))
    all_heads = sorted(m.start() for m in ANY_HEADING_RE.finditer(text))
    out: List[Tuple[int, int, str]] = []
    for h in heads:
        start = h.start()
        end = len(text)
        for hp in all_heads:
            if hp > start:
                end = hp
                break
        uc_id = f"{h.group(1)}.{h.group(2)}.{h.group(3)}"
        out.append((start, end, uc_id))
    return out


def detect_archetype(block: str) -> str:
    # Prefer Detection type → Monitoring type → default
    m = re.search(r"\n- \*\*Detection type:\*\*\s*([^\n]+)", block)
    if m:
        val = m.group(1).strip()
        for key in ARCHETYPES:
            if val.startswith(key):
                return ARCHETYPES[key]
    m = re.search(r"\n- \*\*Monitoring type:\*\*\s*([^\n]+)", block)
    if m:
        val = m.group(1).lower()
        if "security" in val:
            return ARCHETYPES["default"]
        if "performance" in val or "capacity" in val:
            return ARCHETYPES["Operational metrics"]
    return ARCHETYPES["default"]


def insert_kfp(block: str) -> Tuple[str, bool]:
    """If block lacks Known false positives, insert a line above References
    (or above Status/etc metadata) and return new_block."""
    if re.search(r"\n- \*\*Known false positives:\*\*", block):
        return block, False
    line = "- **Known false positives:** " + detect_archetype(block)

    # Preferred insertion: immediately before the References line
    ref = REF_LINE_RE.search(block)
    if ref:
        insert_at = ref.start()
        new_block = block[:insert_at] + line + "\n" + block[insert_at:]
        return new_block, True

    # Else: before Status line
    status = STATUS_LINE_RE.search(block)
    if status:
        insert_at = status.start()
        new_block = block[:insert_at] + line + "\n" + block[insert_at:]
        return new_block, True

    # Else: before the trailing `---`
    sep = SEP_RE.search(block)
    if sep:
        new_block = block[: sep.start()] + line + "\n\n" + block[sep.start() :]
        return new_block, True

    if not block.endswith("\n"):
        block += "\n"
    return block + line + "\n", True


def process_file(path: str, write: bool) -> Tuple[int, int]:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    ranges = split_ucs(original)
    if not ranges:
        return 0, 0
    out: List[str] = []
    cursor = 0
    touched = 0
    for start, end, _uc_id in ranges:
        out.append(original[cursor:start])
        block = original[start:end]
        new_block, changed = insert_kfp(block)
        if changed:
            touched += 1
        out.append(new_block)
        cursor = end
    out.append(original[cursor:])
    new_text = "".join(out)
    if write and new_text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return len(ranges), touched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="persist changes")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    grand_total = 0
    grand_touched = 0
    for path in cat_files:
        cat_prefix = os.path.basename(path)[4:6]
        if cat_prefix not in SECURITY_CATS:
            continue
        total, touched = process_file(path, args.write)
        grand_total += total
        grand_touched += touched
        print(f"  {os.path.basename(path):48}  +{touched:4}/{total} UCs")
    print("-" * 70)
    print(f"Security-cat UCs total: {grand_total}, KFP inserted: {grand_touched}")
    if not args.write:
        print("(dry run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
