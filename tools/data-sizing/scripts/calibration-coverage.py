#!/usr/bin/env python3
"""Emit per-category calibration coverage for the data-sizing catalogue.

Always exit 0 (advisory). The `--check N` mode (where N is a minimum
overall coverage percentage) is reserved for future gating.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CATALOGUE = REPO / "tools" / "data-sizing" / "ot-data-sources.js"
COVERAGE_OUT = REPO / "dist" / "data-sizing-coverage.json"


def extract_catalogue() -> list:
    proc = subprocess.run(
        ["node", "-e",
         "global.window = {};"
         f"require({json.dumps(str(CATALOGUE))});"
         "process.stdout.write(JSON.stringify(global.window.OT_DATA_SOURCES));"],
        capture_output=True, check=True, text=True,
    )
    return json.loads(proc.stdout)


def coverage(sources: list) -> dict:
    overall_total = len(sources)
    overall_calibrated = sum(1 for s in sources if s.get("calibration") == "calibrated")

    by_cat: dict[str, dict[str, int]] = OrderedDict()
    for s in sources:
        cat = s.get("category", "<uncategorised>")
        bucket = by_cat.setdefault(cat, {"total": 0, "calibrated": 0})
        bucket["total"] += 1
        if s.get("calibration") == "calibrated":
            bucket["calibrated"] += 1

    return {
        "overall": {
            "total": overall_total,
            "calibrated": overall_calibrated,
            "percent": (round(overall_calibrated / overall_total * 100, 1)
                        if overall_total else 0.0),
        },
        "by_category": {
            cat: {
                **b,
                "percent": (round(b["calibrated"] / b["total"] * 100, 1)
                            if b["total"] else 0.0),
            }
            for cat, b in by_cat.items()
        },
    }


def print_report(cov: dict) -> None:
    o = cov["overall"]
    print("Data Sizing catalogue calibration coverage")
    print("=" * 42)
    print(f"  calibrated: {o['calibrated']:>3} / {o['total']:<3} ({o['percent']}%)")
    print(f"  pending:    {o['total'] - o['calibrated']:>3} / {o['total']:<3} "
          f"({round(100 - o['percent'], 1)}%)")
    print("")
    print("By category:")
    for cat, b in cov["by_category"].items():
        print(f"  {cat:<42}{b['calibrated']:>3} / {b['total']:<3} ({b['percent']}%)")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", type=float, default=None,
                   help="(future) fail when overall coverage < N percent")
    p.add_argument("--json", action="store_true",
                   help="emit JSON only (no human-readable report)")
    args = p.parse_args()

    sources = extract_catalogue()
    cov = coverage(sources)

    COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_OUT.write_text(json.dumps(cov, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(cov, indent=2))
    else:
        print_report(cov)
        print("")
        print(f"Wrote machine-readable report: {COVERAGE_OUT.relative_to(REPO)}")

    if args.check is not None and cov["overall"]["percent"] < args.check:
        print(f"FAIL: coverage {cov['overall']['percent']}% < required {args.check}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
