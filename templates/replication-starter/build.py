#!/usr/bin/env python3
"""Minimal replication starter build.

Reads every JSON sidecar under ``content/cat-NN-<slug>/UC-X.Y.Z.json`` (the
single source of truth) and emits ``data.js`` (for the dashboard) and
``catalog.json`` (for integrators).

Each category directory must also carry a ``_category.json`` describing the
category's id, display name, and ordered subcategory shells. UC sidecars are
slotted into subcategories by their ``id`` prefix (e.g. ``1.2.3`` lands in
subcategory ``1.2``); a missing subcategory entry creates a stub bucket so
the build never silently drops a UC.

This is the smallest useful build script. The parent repo's
``tools/build/build.py`` extends this pattern with: auto-tagging, derived
fields, LLM index, API shards, sitemap, signed provenance, and release-notes
sync. Start here and layer on what you need.
"""

import glob
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(SCRIPT_DIR, "content")


def parse_category(cat_dir):
    """Parse one ``content/cat-*/`` directory into a category dict."""
    meta_path = os.path.join(cat_dir, "_category.json")
    if not os.path.exists(meta_path):
        return None
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    cid = meta.get("id")
    if cid is None:
        return None
    try:
        cid_int = int(cid)
    except (TypeError, ValueError):
        return None

    cat = {"i": cid_int, "n": meta.get("name", ""), "s": []}
    sub_buckets = {}
    for sub in meta.get("subcategories", []) or []:
        sub_id = sub.get("id")
        if not sub_id:
            continue
        record = {"i": sub_id, "n": sub.get("name", ""), "u": []}
        sub_buckets[sub_id] = record
        cat["s"].append(record)

    for uc_path in sorted(glob.glob(os.path.join(cat_dir, "UC-*.json"))):
        try:
            with open(uc_path, "r", encoding="utf-8") as f:
                uc = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        uid = uc.get("id") or ""
        if not uid:
            continue
        bucket_key = ".".join(uid.split(".")[:2])
        bucket = sub_buckets.get(bucket_key)
        if bucket is None:
            bucket = {"i": bucket_key, "n": "", "u": []}
            sub_buckets[bucket_key] = bucket
            cat["s"].append(bucket)
        bucket["u"].append({
            "i": uid,
            "n": uc.get("title", ""),
            "c": uc.get("criticality", ""),
            "f": uc.get("difficulty", ""),
        })
    return cat


def main():
    cat_dirs = sorted(
        d for d in glob.glob(os.path.join(CONTENT_DIR, "cat-*")) if os.path.isdir(d)
    )
    data = []
    for cat_dir in cat_dirs:
        cat = parse_category(cat_dir)
        if cat is not None:
            data.append(cat)
    total = sum(len(u["u"]) for c in data for u in c["s"])

    with open(os.path.join(SCRIPT_DIR, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"data": data, "total_uc": total}, f, indent=2)

    with open(os.path.join(SCRIPT_DIR, "data.js"), "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f)
        f.write(";\n")

    print(f"Built {len(data)} categories, {total} use cases.")


if __name__ == "__main__":
    main()
