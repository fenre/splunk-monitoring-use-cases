#!/usr/bin/env python3
"""Merge cat-25 research batches into a single expansion manifest."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "scripts" / "cat25_research_manifest.json"
BATCH_1 = REPO / "scripts" / "cat25_1_29_expansion_research.json"

# Researched targets for subs 30-115 (from domain analysis; max 100).
TARGETS_30_115: dict[str, int] = {
    "30": 58, "31": 52, "32": 48, "33": 50, "34": 55, "35": 52, "36": 50, "37": 48,
    "38": 58, "39": 45, "40": 72, "41": 52, "42": 55, "43": 48, "44": 50, "45": 55,
    "46": 52, "47": 55, "48": 58, "49": 50, "50": 52, "51": 48, "52": 48, "53": 50,
    "54": 52, "55": 55, "56": 48, "57": 45, "58": 58, "59": 75,
    "60": 45, "61": 48, "62": 40, "63": 43, "64": 42, "65": 43, "66": 40, "67": 42,
    "68": 46, "69": 40, "70": 42, "71": 45, "72": 42, "73": 40, "74": 44, "75": 42,
    "76": 42, "77": 42, "78": 48, "79": 46, "80": 50, "81": 42, "82": 46, "83": 48,
    "84": 46, "85": 48, "86": 50, "87": 52, "88": 50, "89": 48,
    "90": 62, "91": 48, "92": 52, "93": 70, "94": 50, "95": 46, "96": 44, "97": 50,
    "98": 56, "99": 78, "100": 55, "101": 42, "102": 45, "103": 52, "104": 50,
    "105": 40, "106": 60, "107": 54, "108": 52, "109": 48, "110": 52, "111": 65,
    "112": 50, "113": 46, "114": 42, "115": 48,
}


def _current_counts() -> dict[str, int]:
    from collections import Counter

    counts: Counter[str] = Counter()
    cat = REPO / "content" / "cat-25-personal-hobbyist-monitoring"
    for p in cat.glob("UC-25.*.*.json"):
        m = re.match(r"UC-25\.(\d+)\.", p.name)
        if m:
            counts[m.group(1)] += 1
    return dict(counts)


def main() -> int:
    manifest: dict[str, object] = {"subcategories": {}}
    batch1 = json.loads(BATCH_1.read_text(encoding="utf-8"))
    current = _current_counts()

    for sub in range(1, 30):
        key = str(sub)
        entry = batch1[key]
        manifest["subcategories"][key] = {
            "target": entry["target"],
            "rationale": entry.get("rationale", ""),
            "current": current.get(key, 0),
            "extra_sources": entry.get("extra_sources", []),
            "specials": entry.get("specials", []),
        }

    for key, target in TARGETS_30_115.items():
        manifest["subcategories"][key] = {
            "target": target,
            "rationale": f"Research-driven variable depth (not uniform 28/33); cap 100.",
            "current": current.get(key, 0),
            "extra_sources": [],
            "specials": [],
        }

    total_current = sum(current.values())
    total_target = sum(v["target"] for v in manifest["subcategories"].values())  # type: ignore[union-attr]
    manifest["summary"] = {
        "subcategory_count": len(manifest["subcategories"]),
        "current_total": total_current,
        "target_total": total_target,
        "delta": total_target - total_current,
    }
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(json.dumps(manifest["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
