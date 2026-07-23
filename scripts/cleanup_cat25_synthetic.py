#!/usr/bin/env python3
"""Remove synthetic gap-fill UCs and exact SPL duplicates from cat-25; renumber gap-free.

Deletes use cases whose SPL targets synthetic ``*:metricN`` sourcetypes and carry
generic analytics-template titles (Monthly Rollup, Hour-of-Day Pattern, etc.).
Also removes exact SPL duplicates, keeping the lowest UC ID in each cluster.

After deletion, renumbers every subcategory 25.Y.1..N and updates ``_category.json``.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAT25 = REPO / "content" / "cat-25-personal-hobbyist-monitoring"
CATEGORY = CAT25 / "_category.json"

GENERIC_TITLE_PATTERNS = (
    r" Monthly Rollup$",
    r" Hour-of-Day Pattern$",
    r" High .+ Outliers$",
    r" Rolling 7-Day .+ Average$",
    r" Weekend vs Weekday Split$",
    r" Field Completeness Score$",
    r" Quiet Streak Detection$",
    r" Quarter-over-Quarter Volume$",
    r" Cross-Feed Correlation$",
)

SYNTHETIC_SPL = re.compile(r"sourcetype=\S*:metric\d+", re.I)


def _is_generic_title(title: str) -> bool:
    return any(re.search(p, title) for p in GENERIC_TITLE_PATTERNS)


def _norm_spl(spl: str) -> str:
    return re.sub(r"\s+", " ", (spl or "").lower().strip())


def _uc_sort_key(uc_id: str) -> tuple[int, int]:
    parts = uc_id.split(".")
    return int(parts[1]), int(parts[2])


def load_ucs() -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in sorted(CAT25.glob("UC-25.*.*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append((path, data))
    return rows


def choose_removals(rows: list[tuple[Path, dict]]) -> set[str]:
    remove: set[str] = set()

    # 1) Synthetic metricN + generic analytics title
    for _path, data in rows:
        uc_id = data["id"]
        title = data.get("title", "")
        spl = data.get("spl", "")
        if SYNTHETIC_SPL.search(spl) and _is_generic_title(title):
            remove.add(uc_id)

    # 2) Exact SPL duplicates — keep lowest id per cluster
    by_spl: dict[str, list[str]] = defaultdict(list)
    for _path, data in rows:
        uc_id = data["id"]
        if uc_id in remove:
            continue
        key = _norm_spl(data.get("spl", ""))
        if key:
            by_spl[key].append(uc_id)

    for _key, ids in by_spl.items():
        if len(ids) < 2:
            continue
        keep = min(ids, key=_uc_sort_key)
        for uc_id in ids:
            if uc_id != keep:
                remove.add(uc_id)

    return remove


def renumber_subcategory(sub_num: str, survivors: list[tuple[Path, dict]]) -> int:
    """Rename files and ids gap-free 1..N for one subcategory."""
    survivors.sort(key=lambda row: _uc_sort_key(row[1]["id"]))
    staging: list[tuple[Path, dict, str]] = []
    for new_z, (path, data) in enumerate(survivors, start=1):
        new_id = f"25.{sub_num}.{new_z}"
        data = dict(data)
        data["id"] = new_id
        staging.append((path, data, new_id))

    # Two-phase rename to avoid collisions
    temp_paths: list[tuple[Path, Path, dict, str]] = []
    for idx, (old_path, data, new_id) in enumerate(staging):
        temp = old_path.with_name(f"__tmp_{sub_num}_{idx}.json")
        temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temp_paths.append((old_path, temp, data, new_id))

    for old_path, temp, _data, new_id in temp_paths:
        final = CAT25 / f"UC-{new_id}.json"
        if old_path.exists() and old_path != final:
            old_path.unlink()
        temp.rename(final)

    return len(staging)


def update_category_json(counts: dict[str, int]) -> None:
    cat = json.loads(CATEGORY.read_text(encoding="utf-8"))
    total = 0
    for sub in cat.get("subcategories", []):
        sub_id = sub.get("id", "")
        sub_num = sub_id.split(".")[-1] if sub_id.startswith("25.") else sub_id
        cnt = counts.get(sub_num, 0)
        sub["useCaseCount"] = cnt
        total += cnt
    cat["totalUseCases"] = total
    cat["useCaseCount"] = total
    CATEGORY.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    rows = load_ucs()
    remove = choose_removals(rows)
    print(f"Loaded {len(rows)} cat-25 UCs")
    print(f"Marked for removal: {len(remove)}")

    by_sub: dict[str, list[tuple[Path, dict]]] = defaultdict(list)
    for path, data in rows:
        sub_num = data["id"].split(".")[1]
        if data["id"] not in remove:
            by_sub[sub_num].append((path, data))

    if dry_run:
        print(f"Would retain {sum(len(v) for v in by_sub.values())} UCs across {len(by_sub)} subs")
        return 0

    # Delete removed files first
    for path, data in rows:
        if data["id"] in remove and path.exists():
            path.unlink()

    counts: dict[str, int] = {}
    for sub_num in sorted(by_sub.keys(), key=int):
        counts[sub_num] = renumber_subcategory(sub_num, by_sub[sub_num])

    update_category_json(counts)
    print(f"Retained {sum(counts.values())} UCs across {len(counts)} subcategories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
