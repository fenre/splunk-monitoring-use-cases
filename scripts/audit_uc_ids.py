#!/usr/bin/env python3
"""Audit UC-* IDs in use-cases/cat-*.md for duplicates, gaps, wrong category, order."""

import glob
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

USE_CASES_DIR = "/Users/fsudmann/Documents/GitHub/splunk-monitoring-use-cases/use-cases"
UC_HEADER = re.compile(r"### UC-(\d+)\.(\d+)\.(\d+)")
FILENAME_CAT = re.compile(r"cat-(\d+)-")


def extract_file_category(path: str) -> Optional[int]:
    m = FILENAME_CAT.search(path)
    if not m:
        return None
    return int(m.group(1))


def audit_file(filepath: str) -> List[str]:
    issues: List[str] = []
    expected_cat = extract_file_category(filepath)
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    matches = list(UC_HEADER.finditer(text))
    if not matches:
        return issues

    ordered: List[Tuple[str, int, int, int]] = []
    for m in matches:
        x, y, z = int(m.group(1)), int(m.group(2)), int(m.group(3))
        full = f"UC-{x}.{y}.{z}"
        ordered.append((full, x, y, z))

    counts = Counter(t[0] for t in ordered)
    for uid, c in sorted(counts.items()):
        if c > 1:
            issues.append(f"Duplicate UC ID: {uid} appears {c} times")

    if expected_cat is not None:
        for full, x, _y, _z in ordered:
            if x != expected_cat:
                issues.append(
                    f"Wrong category: {full} has X={x} but file is cat-{expected_cat:02d}-*"
                )

    by_sub: Dict[Tuple[int, int], List[Tuple[str, int]]] = defaultdict(list)
    for full, x, y, z in ordered:
        by_sub[(x, y)].append((full, z))

    for (x, y) in sorted(by_sub.keys()):
        seq = by_sub[(x, y)]
        zs_in_order = [z for _, z in seq]

        for i in range(1, len(zs_in_order)):
            if zs_in_order[i] <= zs_in_order[i - 1]:
                issues.append(
                    f"Out-of-order within subcategory UC-{x}.{y}.*: "
                    f"{seq[i - 1][0]} (Z={zs_in_order[i - 1]}) then "
                    f"{seq[i][0]} (Z={zs_in_order[i]}) — Z does not increase"
                )

        z_set = sorted(set(zs_in_order))
        for a, b in zip(z_set, z_set[1:]):
            if b > a + 1:
                missing = list(range(a + 1, b))
                issues.append(
                    f"Gap in Z for UC-{x}.{y}.*: between Z={a} and Z={b}, missing {missing}"
                )

    return issues


def main() -> int:
    paths = sorted(glob.glob(f"{USE_CASES_DIR}/cat-*.md"))
    all_issues: Dict[str, List[str]] = {}
    for p in paths:
        issues = audit_file(p)
        if issues:
            all_issues[p] = issues

    if not all_issues:
        print("No issues found.")
        return 0

    for p in sorted(all_issues.keys()):
        print(f"\n## {p}")
        for line in all_issues[p]:
            print(f"  - {line}")

    print(f"\n---\nTotal files with issues: {len(all_issues)}")
    total = sum(len(v) for v in all_issues.values())
    print(f"Total issue lines: {total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
