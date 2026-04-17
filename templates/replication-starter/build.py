#!/usr/bin/env python3
"""Minimal replication starter build.

Reads every use-cases/cat-*.md file, parses a fixed heading + bulleted-field
schema, and emits data.js (for the dashboard) and catalog.json (for integrators).

This is the smallest useful build script. The parent repo's build.py extends
this pattern with: auto-tagging, derived fields, LLM index, API shards, sitemap,
and release-notes sync. Start here and layer on what you need.
"""

import glob
import json
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
UC_DIR = os.path.join(SCRIPT_DIR, "use-cases")


def parse_category(path):
    """Parse one cat-*.md file into a category dict."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    cat = {"s": []}
    current_sub = None
    current_uc = None

    for line in content.split("\n"):
        stripped = line.strip()
        m = re.match(r"^#\s+(\d+)\.\s+(.+)$", stripped)
        if m:
            cat["i"] = int(m.group(1))
            cat["n"] = m.group(2).strip()
            continue
        m = re.match(r"^##\s+(\d+\.\d+)\s+(.+)$", stripped)
        if m:
            current_sub = {"i": m.group(1), "n": m.group(2).strip(), "u": []}
            cat["s"].append(current_sub)
            current_uc = None
            continue
        m = re.match(r"^###\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+)$", stripped)
        if m and current_sub is not None:
            current_uc = {"i": m.group(1), "n": m.group(2).strip()}
            current_sub["u"].append(current_uc)
            continue
        m = re.match(r"^-\s+\*\*(.+?):\*\*\s*(.*)$", stripped)
        if m and current_uc is not None:
            current_uc[m.group(1).lower().replace(" ", "_")] = m.group(2).strip()

    return cat


def main():
    files = sorted(glob.glob(os.path.join(UC_DIR, "cat-*.md")))
    data = [parse_category(p) for p in files]
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
