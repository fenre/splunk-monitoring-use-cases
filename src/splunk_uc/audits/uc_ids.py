#!/usr/bin/env python3
"""Audit UC identifier structure and permanent-identity ledger invariants."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from splunk_uc.id_ledger import (
    LEDGER_PATH,
    load_ledger,
    validate_catalogue_against_ledger,
)

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
        expected_fname = f"UC-{uc_id}.json"
        if uc_path.name != expected_fname:
            issues.append(f"{uc_path.name}: filename does not match id ({expected_fname!r})")
        ordered.append((full, x, y, z, uc_path.name))

    counts = Counter(t[0] for t in ordered)
    for uid, c in sorted(counts.items()):
        if c > 1:
            issues.append(f"Duplicate UC ID inside {cat_dir.name}: {uid} appears {c} times")

    for full, x, _y, _z, _fn in ordered:
        if x != expected_cat:
            issues.append(
                f"Wrong category: {full} has X={x} but folder is cat-{expected_cat:02d}-*"
            )

    by_sub: dict[tuple[int, int], list[tuple[str, int]]] = defaultdict(list)
    for full, x, y, z, _fn in ordered:
        by_sub[(x, y)].append((full, z))

    for x, y in sorted(by_sub.keys()):
        zs_in_order = [z for _, z in by_sub[(x, y)]]
        duplicate_z = [z for z, count in Counter(zs_in_order).items() if count > 1]
        for dup_z in sorted(duplicate_z):
            issues.append(
                f"Duplicate Z in subcategory UC-{x}.{y}.*: Z={dup_z} appears more than once"
            )

    return issues


def audit_ledger() -> list[str]:
    if not LEDGER_PATH.is_file():
        return [f"Missing ledger file: {LEDGER_PATH.relative_to(REPO_ROOT)}"]
    try:
        ledger = load_ledger()
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Failed to parse id-ledger.json: {exc}"]
    return validate_catalogue_against_ledger(ledger=ledger)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit UC-* IDs in content/cat-*/UC-*.json for duplicates, wrong category, "
            "filename mismatch, and permanent-identity ledger invariants."
        )
    )
    parser.parse_args(argv)

    cat_dirs = sorted(p for p in CONTENT.iterdir() if p.is_dir() and p.name.startswith("cat-"))
    all_issues: dict[str, list[str]] = {}

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

    ledger_issues = audit_ledger()
    if ledger_issues:
        all_issues["__id_ledger__"] = ledger_issues

    if not all_issues:
        print("No issues found.")
        return 0

    for p in sorted(all_issues.keys()):
        print(f"\n## {p}")
        for line in all_issues[p]:
            print(f"  - {line}")

    print(f"\n---\nTotal categories with issues: {len(all_issues)}")
    total = sum(len(v) for v in all_issues.values())
    print(f"Total issue lines: {total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
