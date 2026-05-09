#!/usr/bin/env python3
"""One-shot patch: backfill `g` (guide) field on every subcategory in
`catalog.json` from each category's `_category.json`. Does not touch
any UC content.

The committed `catalog.json` is the SSOT for the SPA. Until the
modular build pipeline owns its regeneration, this script keeps
`catalog.json` in sync with the wiring layer (`_category.json` files)
that the modular build already consumes.

Idempotent: re-running with no `_category.json` changes produces a
zero-diff output.

Run from repo root:
    python3 scripts/_patch_catalog_guide_fields.py
"""
from __future__ import annotations

import json
from pathlib import Path

CATALOG_PATH = Path("catalog.json")
CONTENT_DIR = Path("content")


def _load_subcategory_guides() -> dict[int, dict[str, str]]:
    """Return ``{cat_id: {sub_id: guide_path}}``."""
    out: dict[int, dict[str, str]] = {}
    for cat_dir in sorted(CONTENT_DIR.glob("cat-*")):
        meta_path = cat_dir / "_category.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        cat_id = meta.get("id")
        if cat_id is None:
            continue
        sub_map: dict[str, str] = {}
        for sub in meta.get("subcategories", []) or []:
            sid = sub.get("id")
            guide = sub.get("guide")
            if sid and guide:
                sub_map[sid] = guide
        if sub_map:
            out[int(cat_id)] = sub_map
    return out


def main() -> None:
    if not CATALOG_PATH.exists():
        print(f"!! {CATALOG_PATH} missing — nothing to patch")
        return

    cat = json.loads(CATALOG_PATH.read_text())
    sub_guides = _load_subcategory_guides()
    patched = 0
    unchanged = 0

    for cat_entry in cat.get("DATA", []):
        cid = cat_entry.get("i")
        if cid is None:
            continue
        for sub in cat_entry.get("s", []):
            sid = str(sub.get("i", ""))
            guide = sub_guides.get(int(cid), {}).get(sid)
            if guide:
                if sub.get("g") != guide:
                    sub["g"] = guide
                    patched += 1
                else:
                    unchanged += 1

    CATALOG_PATH.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n")
    print(f"patched {patched} subcategories, {unchanged} already in sync")


if __name__ == "__main__":
    main()
