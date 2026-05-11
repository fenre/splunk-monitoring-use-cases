#!/usr/bin/env python3
"""Apply data/uc-link-fallbacks.json to every UC JSON file: swap dead
reference URLs for their verified fallback ancestor or curated host
fallback. Pass --write to apply; default is dry-run.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
FALLBACKS = REPO / "data" / "uc-link-fallbacks.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fb = json.loads(FALLBACKS.read_text())["fallbacks"]
    fallback_map = {u: v["fallback"] for u, v in fb.items() if v.get("fallback")}
    if not fallback_map:
        print("No fallbacks available — run scripts/find_url_fallbacks.py first.", file=sys.stderr)
        return 1

    total_files = 0
    total_swaps = 0
    samples: list[tuple[str, str, str]] = []

    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        changed = False
        refs = d.get("references")
        if not isinstance(refs, list):
            continue
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            u = ref.get("url")
            if not isinstance(u, str):
                continue
            u_clean = u.strip().rstrip(".,;)]\\")
            target = fallback_map.get(u_clean) or fallback_map.get(u)
            if target and target != u:
                if len(samples) < 5:
                    samples.append((p.name, u, target))
                ref["url"] = target
                # If retrievedDate exists, refresh to current
                if "retrieved" in ref:
                    ref["retrieved"] = "2026-05-11"
                changed = True
                total_swaps += 1
        if changed:
            total_files += 1
            if args.write:
                p.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"Files affected: {total_files}")
    print(f"URLs swapped: {total_swaps}")
    print("\nSamples:")
    for f, old, new in samples:
        print(f"  [{f}] {old}\n              -> {new}")
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
