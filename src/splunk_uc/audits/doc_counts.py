#!/usr/bin/env python3
"""Doc freshness audit — checks that numeric claims in key docs are within tolerance of actual counts."""

from __future__ import annotations

import pathlib
import re
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]


def get_actual_uc_count() -> int:
    """Count UC JSON files in content/."""
    return len(list((PROJECT_ROOT / "content").rglob("UC-*.json")))


def get_actual_category_count() -> int:
    """Count category directories."""
    return len(list((PROJECT_ROOT / "content").glob("cat-*")))


CHECKS = [
    ("AGENTS.md", r"(\d[\d,]+)\+?\s*(?:use[- ]cases|UCs)", "uc_count"),
    ("docs/PITCH.md", r"(\d[\d,]+)\+?\s*(?:use[- ]cases|UCs)", "uc_count"),
    ("docs/architecture.md", r"(\d[\d,]+)\+?\s*(?:use[- ]cases|UCs)", "uc_count"),
]


def main(argv: list[str] | None = None) -> int:
    del argv
    actual_ucs = get_actual_uc_count()
    tolerance = 0.05
    warnings = []

    for rel_path, pattern, check_type in CHECKS:
        fpath = PROJECT_ROOT / rel_path
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        for m in re.finditer(pattern, text, re.IGNORECASE):
            claimed = int(m.group(1).replace(",", ""))
            if check_type == "uc_count" and abs(claimed - actual_ucs) / actual_ucs > tolerance:
                warnings.append(
                    f"{rel_path}: claims {claimed} UCs, actual is {actual_ucs} "
                    f"(>{tolerance * 100:.0f}% drift)"
                )

    if warnings:
        print(f"Doc freshness: {len(warnings)} stale count(s):", file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)
        return 1

    print(
        f"Doc freshness: all checked counts within {tolerance * 100:.0f}% of actual "
        f"({actual_ucs} UCs)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
