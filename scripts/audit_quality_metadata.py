#!/usr/bin/env python3
"""Audit per-UC quality metadata coverage.

Runs after build.py has produced catalog.json. Reports coverage % of:
  - Status:          (verified | community | draft)
  - Last reviewed:   (ISO date)
  - Splunk versions: (free text)
  - Reviewer:        (handle or N/A)
  - References:      (URLs)
  - Known false positives:

Usage:
    python3 scripts/audit_quality_metadata.py           # warn-only
    python3 scripts/audit_quality_metadata.py --strict  # exit 1 if any coverage below thresholds

Default thresholds (warn-only in v5.1, gating from v5.2+):
    References:      100%  (new UCs must include)
    Status:           50%  (verified/community/draft tag)
    Last reviewed:    30%
    Splunk versions:  25%
    Reviewer:         25%
    Known FP (cats 9/10/14/17/22): 60%
"""

from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CATALOG = os.path.join(REPO_ROOT, "catalog.json")

SECURITY_CATS = {9, 10, 14, 17, 22}

THRESHOLDS: Dict[str, float] = {
    "refs": 100.0,    # References — every UC should have one
    "status": 50.0,
    "reviewed": 30.0,
    "sver": 25.0,
    "rby": 25.0,
    "kfp_security": 60.0,   # Known FP on security-relevant categories
}

FIELD_LABEL: Dict[str, str] = {
    "refs": "References",
    "status": "Status",
    "reviewed": "Last reviewed",
    "sver": "Splunk versions",
    "rby": "Reviewer",
    "kfp_security": "Known false positives (security cats)",
}


def load_catalog() -> dict:
    if not os.path.exists(CATALOG):
        print(f"FAIL: {CATALOG} not found. Run python3 build.py first.", file=sys.stderr)
        sys.exit(2)
    with open(CATALOG, "r", encoding="utf-8") as f:
        return json.load(f)


def iter_ucs(catalog: dict):
    for cat in catalog.get("DATA", []):
        cat_id = cat.get("i", 0)
        for sub in cat.get("s", []):
            for uc in sub.get("u", []):
                yield cat_id, uc


def compute_coverage(catalog: dict) -> Tuple[Dict[str, Dict[str, int]], int, int]:
    total = 0
    sec_total = 0
    counts: Dict[str, Dict[str, int]] = {
        k: {"present": 0} for k in FIELD_LABEL
    }
    for cat_id, uc in iter_ucs(catalog):
        total += 1
        is_sec = cat_id in SECURITY_CATS
        if is_sec:
            sec_total += 1
        for key in ("refs", "status", "reviewed", "sver", "rby"):
            val = uc.get(key)
            if isinstance(val, str) and val.strip():
                counts[key]["present"] += 1
            elif isinstance(val, list) and val:
                counts[key]["present"] += 1
        if is_sec:
            kfp = uc.get("kfp", "")
            if isinstance(kfp, str) and kfp.strip():
                counts["kfp_security"]["present"] += 1
    return counts, total, sec_total


def main() -> int:
    strict = "--strict" in sys.argv
    catalog = load_catalog()
    counts, total, sec_total = compute_coverage(catalog)

    print(f"Quality metadata coverage — total UCs: {total} (security-cat UCs: {sec_total})")
    print("-" * 70)
    failed: List[str] = []
    for field, label in FIELD_LABEL.items():
        present = counts[field]["present"]
        denom = sec_total if field == "kfp_security" else total
        pct = (present / denom * 100.0) if denom else 0.0
        threshold = THRESHOLDS[field]
        status = "OK" if pct >= threshold else "BELOW"
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"  {label:<40} [{bar}] {pct:5.1f}%  ({present}/{denom})  target {threshold:5.1f}%  {status}")
        if pct < threshold:
            failed.append(f"{label}: {pct:.1f}% < {threshold:.1f}%")

    print("-" * 70)
    if failed:
        print(f"{len(failed)} coverage target(s) below threshold:")
        for m in failed:
            print(f"  - {m}")
        if strict:
            return 1
        print("(warn-only; pass --strict to fail)")
        return 0

    print("All coverage targets met.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
