#!/usr/bin/env python3
"""Register new cat-25 subcategories in _category.json."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT = REPO / "content" / "cat-25-personal-hobbyist-monitoring" / "_category.json"


def add_subcategories(new_subs: list[dict]) -> None:
    data = json.loads(CAT.read_text(encoding="utf-8"))
    existing = {s["id"] for s in data["subcategories"]}
    for sub in new_subs:
        sid = sub["id"]
        if sid in existing:
            for i, s in enumerate(data["subcategories"]):
                if s["id"] == sid:
                    data["subcategories"][i].update(sub)
                    break
        else:
            data["subcategories"].append(sub)
    data["subcategories"].sort(key=lambda s: [int(x) for x in s["id"].split(".")[1:]])
    from collections import Counter
    import re

    counts = Counter()
    for p in (REPO / "content/cat-25-personal-hobbyist-monitoring").glob("UC-25.*.*.json"):
        m = re.match(r"UC-25\.(\d+)\.", p.name)
        if m:
            counts[m.group(1)] += 1
    for s in data["subcategories"]:
        num = s["id"].split(".")[1]
        s["useCaseCount"] = counts.get(num, s.get("useCaseCount", 0))
    data["useCaseCount"] = sum(counts.values())
    CAT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated _category.json: {data['useCaseCount']} UCs, {len(data['subcategories'])} subcategories")


if __name__ == "__main__":
    import sys
    add_subcategories(json.loads(sys.stdin.read()))
