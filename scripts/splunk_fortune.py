#!/usr/bin/env python3
"""
Splunk fortune cookie — pick a random monitoring use case from catalog.json
and print it with a little flair. Run from repo root:

    python3 scripts/splunk_fortune.py

Optional: --count N for N random picks.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

COOKIE = r"""
     .--------.
    /  Your   /\
   /  SPLunk  /  \
  /  fortune  /   \
 '-----------'    '
  \  \  \  \  \  \  \
"""

FALLBACK = [
    {
        "n": "Emergency SPL",
        "c": "high",
        "v": "When in doubt, index=* | head 100",
        "q": "index=* | head 100",
    }
]


def load_catalog(path: Path) -> list[dict]:
    if not path.is_file():
        return FALLBACK
    with path.open(encoding="utf-8") as f:
        root = json.load(f)
    flat: list[dict] = []
    for block in root.get("DATA", []):
        for cat in block.get("s", []):
            cat_name = cat.get("n", "?")
            for uc in cat.get("u", []):
                uc["_category"] = cat_name
                flat.append(uc)
    return flat or FALLBACK


def fortune_line(uc: dict) -> str:
    crit = uc.get("c", "?")
    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(crit, "⚪")
    return f"{emoji} [{crit}] {uc.get('_category', '')} → {uc.get('n', 'Untitled')}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Random Splunk monitoring fortune from catalog.json")
    ap.add_argument("--count", "-n", type=int, default=1, help="How many fortunes (default 1)")
    ap.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "catalog.json",
        help="Path to catalog.json",
    )
    args = ap.parse_args()

    use_cases = load_catalog(args.catalog)
    picks = random.sample(use_cases, min(args.count, len(use_cases)))

    print(COOKIE)
    for uc in picks:
        print()
        print(fortune_line(uc))
        print(f"   {uc.get('v', '').strip()[:200]}{'…' if len(uc.get('v', '')) > 200 else ''}")
        q = uc.get("q", "").strip()
        if q:
            print()
            print("   ── sample SPL ──")
            for line in q.split("\n")[:8]:
                print(f"   {line}")
            if q.count("\n") > 7:
                print("   …")
        print()

    print("  May your pipelines be fast and your _raw never truncated. 🥠\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
