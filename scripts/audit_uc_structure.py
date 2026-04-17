#!/usr/bin/env python3
"""Audit use-case markdown blocks in use-cases/cat-*.md for required structure."""
from __future__ import annotations

import glob
import os
import random
import re
import argparse
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES = os.path.join(REPO_ROOT, "use-cases", "cat-*.md")

LARGE_THRESHOLD = 5000
SAMPLE_SIZE = 200

VALID_CRITICALITY = frozenset(
    {"🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"}
)
VALID_DIFFICULTY = frozenset(
    {"🟢 Beginner", "🔵 Intermediate", "🟠 Advanced", "🔴 Expert"}
)

REQUIRED_FIELDS = [
    "Criticality",
    "Difficulty",
    "Monitoring type",
    "Value",
    "App/TA",
    "Data Sources",
    "SPL",
    "Implementation",
    "Visualization",
    "CIM Models",
]

RE_UC_HEAD = re.compile(
    r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE
)
RE_FIELD_LINE = re.compile(
    r"^\s*-\s*\*\*([^*]+):\*\*\s*(.*)$"
)


@dataclass
class UCParse:
    uc_id: str
    file_path: str
    title: str
    body: str
    fields: dict = field(default_factory=dict)
    spl_fenced: Optional[str] = None


def split_uc_blocks(text: str, file_path: str) -> List[UCParse]:
    matches = list(RE_UC_HEAD.finditer(text))
    if not matches:
        return []
    out: List[UCParse] = []
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        out.append(UCParse(uc_id=uc_id, file_path=file_path, title=title, body=body))
    return out


def extract_field_lines(body: str) -> dict:
    fields: dict = {}
    for line in body.splitlines():
        mm = RE_FIELD_LINE.match(line)
        if mm:
            name = mm.group(1).strip()
            val = mm.group(2).strip()
            if name not in fields:
                fields[name] = val
    return fields


RE_SPL_MARKER = re.compile(r"-\s+\*\*SPL(?:\s*\([^)]*\))?:\*\*")


def extract_spl_fenced(body: str) -> Tuple[Optional[str], str]:
    m = RE_SPL_MARKER.search(body)
    if m is None:
        return None, "no_SPL_marker"

    rest = body[m.end():]
    lines = rest.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return None, "no_fence_after_SPL"

    fence_start = lines[i].strip()
    if not fence_start.startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or not lines[i].strip().startswith("```"):
            return None, "no_opening_fence_after_SPL"
        fence_start = lines[i].strip()

    inner_lines: List[str] = []
    i += 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "```":
            return "\n".join(inner_lines), ""
        inner_lines.append(line)
        i += 1
    return None, "unclosed_fence_after_SPL"


def audit_uc(uc: UCParse) -> List[str]:
    issues: List[str] = []
    uc.fields = extract_field_lines(uc.body)
    spl_content, spl_err = extract_spl_fenced(uc.body)
    uc.spl_fenced = spl_content

    for fname in REQUIRED_FIELDS:
        if fname == "SPL":
            continue
        if fname not in uc.fields:
            issues.append(f"{uc.uc_id}: missing field **{fname}:**")
        else:
            v = uc.fields[fname].strip()
            if not v:
                issues.append(f"{uc.uc_id}: empty field **{fname}:**")

    if spl_err:
        issues.append(f"{uc.uc_id}: SPL block problem ({spl_err})")
    elif spl_content is not None:
        if not spl_content.strip():
            issues.append(f"{uc.uc_id}: SPL code block is empty")
    else:
        issues.append(f"{uc.uc_id}: could not parse SPL fenced block")

    crit = uc.fields.get("Criticality", "").strip()
    if crit and crit not in VALID_CRITICALITY:
        issues.append(
            f"{uc.uc_id}: invalid **Criticality:** {crit!r} (expected one of {sorted(VALID_CRITICALITY)})"
        )

    diff = uc.fields.get("Difficulty", "").strip()
    if diff and diff not in VALID_DIFFICULTY:
        issues.append(
            f"{uc.uc_id}: invalid **Difficulty:** {diff!r} (expected one of {sorted(VALID_DIFFICULTY)})"
        )

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit UC markdown structure in cat-*.md")
    ap.add_argument(
        "--full",
        action="store_true",
        help="Check every UC (ignore 5000+ sampling rule)",
    )
    args = ap.parse_args()

    paths = sorted(glob.glob(USE_CASES))
    all_ucs: List[UCParse] = []
    per_file_counts: List[Tuple[str, int]] = []

    for p in paths:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        blocks = split_uc_blocks(text, p)
        per_file_counts.append((os.path.basename(p), len(blocks)))
        all_ucs.extend(blocks)

    total = len(all_ucs)
    seed = 42
    if args.full or total <= LARGE_THRESHOLD:
        to_check = all_ucs
        sampled = False
    else:
        random.seed(seed)
        to_check = random.sample(all_ucs, min(SAMPLE_SIZE, total))
        sampled = True

    all_issues: List[str] = []
    for uc in to_check:
        all_issues.extend(audit_uc(uc))

    print("=" * 72)
    print("UC structure audit (use-cases/cat-*.md)")
    print("=" * 72)
    print(f"Files scanned: {len(paths)}")
    print(f"Total UC blocks parsed: {total}")
    if sampled:
        print(
            f"Sampling: {len(to_check)} UCs checked (random seed={seed}, population>{LARGE_THRESHOLD})"
        )
    elif args.full and total > LARGE_THRESHOLD:
        print(f"Full scan: all {total} UCs checked (--full, population>{LARGE_THRESHOLD})")
    else:
        print(f"All {total} UCs checked (population at or under threshold {LARGE_THRESHOLD})")
    print()
    print("UC counts per file:")
    for name, c in per_file_counts:
        print(f"  {c:5d}  {name}")
    print(f"  {'─' * 40}")
    print(f"  {total:5d}  TOTAL")
    print()
    print(f"Total issues found (in checked set): {len(all_issues)}")
    print()
    if all_issues:
        print("COMPLETE ISSUE LIST (checked set):")
        print("-" * 72)
        for line in all_issues:
            print(line)
    else:
        print("No issues found in the checked set.")

    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
