#!/usr/bin/env python3
"""Repair UCs whose `spl` field contains multiple SPL snippets glued
together by markdown code fences (```...```spl).

Strategy: keep only the FIRST snippet (anything before the first ```
fence).  The other snippets are companion queries; move them into the
detailedImplementation field as a clearly-labelled "Companion queries"
block so the operator still has them.

Pass --write to apply.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"


def split_markdown_spl(spl: str) -> tuple[str, list[str]]:
    """Return (primary_spl, companion_snippets).

    The primary SPL is everything before the first ``` fence.
    Companion snippets are everything between ```spl … ``` fences.
    """
    # Strip leading/trailing whitespace from primary.
    parts = spl.split("```")
    primary = parts[0].rstrip()
    companions: list[str] = []
    for i in range(1, len(parts)):
        seg = parts[i]
        # leading language tag (e.g. "spl\n")
        if seg.startswith("spl"):
            seg = seg[3:]
        seg = seg.strip()
        if seg:
            companions.append(seg)
    return primary, companions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fixed = 0
    samples: list[str] = []
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        spl = d.get("spl")
        if not isinstance(spl, str) or "```" not in spl:
            continue
        primary, companions = split_markdown_spl(spl)
        if not primary:
            continue
        d["spl"] = primary
        if companions:
            extra_block = (
                "\n\nCompanion SPL queries (originally embedded in `spl` field; "
                "kept here for operator reference, run separately):\n\n"
            )
            for idx, c in enumerate(companions, 1):
                extra_block += f"Companion query {idx}:\n```\n{c}\n```\n\n"
            d_imp = d.get("detailedImplementation")
            if isinstance(d_imp, str) and "Companion SPL queries" not in d_imp:
                d["detailedImplementation"] = d_imp.rstrip() + extra_block
        if args.write:
            p.write_text(
                json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        fixed += 1
        if len(samples) < 5:
            samples.append(
                f"  [{p.name}] kept primary ({len(primary)} chars), moved {len(companions)} companion(s) to detailedImplementation"
            )

    print(f"Files fixed: {fixed}")
    for s in samples:
        print(s)
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
