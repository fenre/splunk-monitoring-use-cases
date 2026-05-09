#!/usr/bin/env python3
"""Audit UC-* IDs in use-cases/cat-*.md for duplicates, gaps, wrong category, order."""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import pairwise

# parents[3] resolves: uc_ids.py -> audits/ -> splunk_uc/ -> src/ ->
# repo root. The legacy ``parent.parent`` chain assumed a one-level
# depth and is now wrong by three.
REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)),
        ),
    ),
)
USE_CASES_DIR = os.path.join(REPO_ROOT, "use-cases")
UC_HEADER = re.compile(r"### UC-(\d+)\.(\d+)\.(\d+)")
FILENAME_CAT = re.compile(r"cat-(\d+)-")


def extract_file_category(path: str) -> int | None:
    m = FILENAME_CAT.search(path)
    if not m:
        return None
    return int(m.group(1))


def audit_file(filepath: str) -> list[str]:
    issues: list[str] = []
    expected_cat = extract_file_category(filepath)
    with open(filepath, encoding="utf-8") as fh:
        text = fh.read()

    matches = list(UC_HEADER.finditer(text))
    if not matches:
        return issues

    ordered: list[tuple[str, int, int, int]] = []
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

    by_sub: dict[tuple[int, int], list[tuple[str, int]]] = defaultdict(list)
    for full, x, y, z in ordered:
        by_sub[(x, y)].append((full, z))

    for x, y in sorted(by_sub.keys()):
        seq = by_sub[(x, y)]
        zs_in_order = [z for _, z in seq]

        for i in range(1, len(zs_in_order)):
            if zs_in_order[i] <= zs_in_order[i - 1]:
                issues.append(
                    f"Out-of-order within subcategory UC-{x}.{y}.*: "
                    f"{seq[i - 1][0]} (Z={zs_in_order[i - 1]}) then "
                    f"{seq[i][0]} (Z={zs_in_order[i]}) - Z does not increase"
                )

        z_set = sorted(set(zs_in_order))
        for a, b in pairwise(z_set):
            if b > a + 1:
                missing = list(range(a + 1, b))
                issues.append(
                    f"Gap in Z for UC-{x}.{y}.*: between Z={a} and Z={b}, missing {missing}"
                )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit UC-* IDs in use-cases/cat-*.md for duplicates, gaps, wrong category, and order."
        )
    )
    parser.add_argument(
        "--warn-gaps",
        action="store_true",
        help="When the only issues are gaps in Z within a subcategory, exit 0.",
    )
    args = parser.parse_args(argv)
    warn_only = args.warn_gaps

    paths = sorted(glob.glob(f"{USE_CASES_DIR}/cat-*.md"))
    all_issues: dict[str, list[str]] = {}
    for p in paths:
        issues = audit_file(p)
        if issues:
            all_issues[p] = issues

    if not all_issues:
        print("No issues found.")
        return 0

    gap_only = all(all(line.startswith("Gap in Z") for line in v) for v in all_issues.values())

    for p in sorted(all_issues.keys()):
        print(f"\n## {p}")
        for line in all_issues[p]:
            print(f"  - {line}")

    print(f"\n---\nTotal files with issues: {len(all_issues)}")
    total = sum(len(v) for v in all_issues.values())
    print(f"Total issue lines: {total}")

    if gap_only and warn_only:
        print("\n(--warn-gaps: gaps treated as warnings, not errors)")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
