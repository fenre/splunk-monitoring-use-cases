#!/usr/bin/env python3
"""Audit UC-* IDs in the JSON SSOT for duplicates, gaps, wrong category, order.

Pre-v8.2.0 this audit walked ``use-cases/cat-*.md`` and parsed ``### UC-X.Y.Z``
headers. The legacy markdown corpus is gone; the JSON SSOT
(``content/cat-*/UC-*.json``) is now the only source.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT = REPO_ROOT / "content"

FILENAME_CAT = re.compile(r"cat-(\d+)-")
ID_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def extract_dir_category(dirname: str) -> int | None:
    m = FILENAME_CAT.search(dirname)
    if not m:
        return None
    return int(m.group(1))


def audit_category(cat_dir: Path) -> list[str]:
    """Walk a single cat-NN-*/ folder and validate every UC sidecar."""
    issues: list[str] = []
    expected_cat = extract_dir_category(cat_dir.name)
    if expected_cat is None:
        return issues

    ordered: list[tuple[str, int, int, int, str]] = []
    for uc_path in sorted(cat_dir.glob("UC-*.json")):
        try:
            with uc_path.open(encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"{uc_path.name}: failed to parse ({exc})")
            continue
        uc_id = str(payload.get("id", "")).strip()
        if not uc_id:
            issues.append(f"{uc_path.name}: missing or empty `id` field")
            continue
        m = ID_PATTERN.match(uc_id)
        if not m:
            issues.append(f"{uc_path.name}: id {uc_id!r} does not match X.Y.Z grammar")
            continue
        x, y, z = int(m.group(1)), int(m.group(2)), int(m.group(3))
        full = f"UC-{x}.{y}.{z}"
        # Filename invariant: UC-<id>.json
        expected_fname = f"UC-{uc_id}.json"
        if uc_path.name != expected_fname:
            issues.append(f"{uc_path.name}: filename does not match id ({expected_fname!r})")
        ordered.append((full, x, y, z, uc_path.name))

    # Duplicates within this category folder
    counts = Counter(t[0] for t in ordered)
    for uid, c in sorted(counts.items()):
        if c > 1:
            issues.append(f"Duplicate UC ID inside {cat_dir.name}: {uid} appears {c} times")

    # Wrong-category check (X must equal cat folder number)
    for full, x, _y, _z, _fn in ordered:
        if x != expected_cat:
            issues.append(
                f"Wrong category: {full} has X={x} but folder is cat-{expected_cat:02d}-*"
            )

    # Per-subcategory ordering and gaps
    by_sub: dict[tuple[int, int], list[tuple[str, int]]] = defaultdict(list)
    for full, x, y, z, _fn in ordered:
        by_sub[(x, y)].append((full, z))

    for x, y in sorted(by_sub.keys()):
        seq = by_sub[(x, y)]
        # Sort by Z so we can audit ordering and find gaps without
        # depending on filesystem sort order — JSON sidecars don't have
        # an intrinsic order in the filesystem the way `### UC-` blocks
        # in a single markdown file did.
        seq_sorted = sorted(seq, key=lambda x: x[1])
        zs_in_order = [z for _, z in seq_sorted]

        z_set = sorted(set(zs_in_order))
        for a, b in pairwise(z_set):
            if b > a + 1:
                missing = list(range(a + 1, b))
                issues.append(
                    f"Gap in Z for UC-{x}.{y}.*: between Z={a} and Z={b}, missing {missing}"
                )

        # Duplicate Z (same id appearing twice with the same Z)
        duplicate_z = [z for z, count in Counter(zs_in_order).items() if count > 1]
        for dup_z in sorted(duplicate_z):
            issues.append(
                f"Duplicate Z in subcategory UC-{x}.{y}.*: Z={dup_z} appears more than once"
            )

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit UC-* IDs in content/cat-*/UC-*.json for duplicates, gaps, "
            "wrong category, filename mismatch."
        )
    )
    parser.add_argument(
        "--warn-gaps",
        action="store_true",
        help="When the only issues are gaps in Z within a subcategory, exit 0.",
    )
    args = parser.parse_args(argv)
    warn_only = args.warn_gaps

    cat_dirs = sorted(p for p in CONTENT.iterdir() if p.is_dir() and p.name.startswith("cat-"))

    all_issues: dict[str, list[str]] = {}

    # Cross-category global uniqueness — UC IDs must be unique repo-wide,
    # not just within a single category folder.
    global_ids: dict[str, list[str]] = defaultdict(list)
    for cd in cat_dirs:
        for uc_path in sorted(cd.glob("UC-*.json")):
            try:
                with uc_path.open(encoding="utf-8") as fh:
                    payload = json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
            uc_id = str(payload.get("id", "")).strip()
            if uc_id:
                global_ids[uc_id].append(os.path.relpath(uc_path, REPO_ROOT))

    cross_dups: list[str] = []
    for uid, locations in sorted(global_ids.items()):
        if len(locations) > 1:
            cross_dups.append(f"UC id {uid!r} appears in multiple sidecars: {', '.join(locations)}")
    if cross_dups:
        all_issues["__cross_category__"] = cross_dups

    for cd in cat_dirs:
        issues = audit_category(cd)
        if issues:
            all_issues[str(cd.relative_to(REPO_ROOT))] = issues

    if not all_issues:
        print("No issues found.")
        return 0

    gap_only = all(all(line.startswith("Gap in Z") for line in v) for v in all_issues.values())

    for p in sorted(all_issues.keys()):
        print(f"\n## {p}")
        for line in all_issues[p]:
            print(f"  - {line}")

    print(f"\n---\nTotal categories with issues: {len(all_issues)}")
    total = sum(len(v) for v in all_issues.values())
    print(f"Total issue lines: {total}")

    if gap_only and warn_only:
        print("\n(--warn-gaps: gaps treated as warnings, not errors)")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
