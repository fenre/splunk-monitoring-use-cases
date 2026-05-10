#!/usr/bin/env python3
"""Audit ``non-technical-view.js`` against the JSON SSOT (``content/cat-*/``).

Cross-checks plain-language coverage in ``non-technical-view.js`` versus
the technical UC corpus:

(a) Every UC ID referenced from JS exists in some ``content/cat-*/UC-*.json``
    sidecar.
(b) Every category folder ``content/cat-NN-*/`` has a top-level entry in JS.
(c) Every subcategory derived from any UC's ``X.Y.Z`` id has at least one
    representative UC (id prefix ``X.Y.``) in the matching JS area.
(d) Every JS top-level numeric category key has a matching content folder.

Pre-v8.2.0 this audit walked the legacy monolithic markdown corpus
(``use-cases/cat-*.md``) for category and subcategory derivation. That
corpus is gone; the JSON SSOT is now the only source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# parents[3] resolves: non_technical_sync.py -> audits/ -> splunk_uc/ ->
# src/ -> repo root.
REPO = Path(__file__).resolve().parents[3]
JS_PATH = REPO / "non-technical-view.js"
CONTENT = REPO / "content"

RE_ID = re.compile(r'id:\s*"(\d+)\.(\d+)\.(\d+)"')
RE_CAT_DIR = re.compile(r"^cat-(\d{2})-")


def extract_top_level_string_keys(js_text: str) -> list[str]:
    """Find quoted string keys immediately under
    ``window.NON_TECHNICAL = { ... }`` at depth 1."""
    m = re.search(r"window\.NON_TECHNICAL\s*=\s*\{", js_text)
    if not m:
        raise ValueError("window.NON_TECHNICAL = { not found")
    i = m.end() - 1
    depth = 0
    keys: list[str] = []
    n = len(js_text)
    while i < n:
        c = js_text[i]
        if c == '"':
            if depth == 1:
                j = i + 1
                while j < n and js_text[j] != '"':
                    if js_text[j] == "\\":
                        j += 2
                        continue
                    j += 1
                key = js_text[i + 1 : j]
                rest = j + 1
                while rest < n and js_text[rest] in " \t":
                    rest += 1
                if rest < n and js_text[rest] == ":":
                    rest += 1
                    while rest < n and js_text[rest] in " \t":
                        rest += 1
                    if rest < n and js_text[rest] == "{":
                        keys.append(key)
                i = j + 1
                continue
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return keys


def parse_js_category_blocks(js_text: str) -> dict[str, str]:
    """Return map ``category_key -> substring of that category's object``."""
    m = re.search(r"window\.NON_TECHNICAL\s*=\s*\{", js_text)
    if not m:
        raise ValueError("window.NON_TECHNICAL = { not found")
    start = m.end() - 1
    depth = 0
    i = start
    n = len(js_text)
    blocks: dict[str, str] = {}
    cat_key: str | None = None
    block_start = -1

    while i < n:
        c = js_text[i]
        if c == '"' and depth == 1 and cat_key is None:
            j = i + 1
            while j < n and js_text[j] != '"':
                if js_text[j] == "\\":
                    j += 2
                    continue
                j += 1
            key = js_text[i + 1 : j]
            rest = j + 1
            while rest < n and js_text[rest] in " \t":
                rest += 1
            if rest < n and js_text[rest] == ":":
                rest += 1
                while rest < n and js_text[rest] in " \t":
                    rest += 1
                if rest < n and js_text[rest] == "{":
                    cat_key = key
                    block_start = rest
                    depth = 2
                    i = rest + 1
                    continue
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 1 and cat_key is not None and block_start >= 0:
                blocks[cat_key] = js_text[block_start:i]
                cat_key = None
                block_start = -1
            elif depth == 0:
                break
        i += 1
    return blocks


def collect_ssot_categories() -> tuple[dict[int, Path], dict[int, set[str]], dict[int, set[str]]]:
    """Walk ``content/cat-NN-*/`` and return:

    * ``cat_dir_by_num``  — category number → folder Path
    * ``ssot_uc_by_cat``  — category number → set of full UC ids ``X.Y.Z``
    * ``ssot_subcats_by_cat`` — category number → set of subcategory keys ``X.Y``
    """
    cat_dir_by_num: dict[int, Path] = {}
    ssot_uc_by_cat: dict[int, set[str]] = defaultdict(set)
    ssot_subcats_by_cat: dict[int, set[str]] = defaultdict(set)

    for d in sorted(CONTENT.glob("cat-*")):
        if not d.is_dir():
            continue
        m = RE_CAT_DIR.match(d.name)
        if not m:
            continue
        cat_num = int(m.group(1))
        if cat_num == 0:
            continue
        cat_dir_by_num[cat_num] = d

        for uc_path in sorted(d.glob("UC-*.json")):
            try:
                with uc_path.open(encoding="utf-8") as fh:
                    uc = json.load(fh)
            except (json.JSONDecodeError, OSError):
                continue
            uc_id = str(uc.get("id", "")).strip()
            if not re.match(r"^\d+\.\d+\.\d+$", uc_id):
                continue
            x, y, _z = uc_id.split(".")
            if int(x) != cat_num:
                continue
            ssot_uc_by_cat[cat_num].add(uc_id)
            ssot_subcats_by_cat[cat_num].add(f"{x}.{y}")

    return cat_dir_by_num, ssot_uc_by_cat, ssot_subcats_by_cat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit non-technical-view.js category/subcategory/UC coverage "
            "against the JSON SSOT (content/cat-*/UC-*.json)."
        )
    )
    parser.parse_args(argv)

    js_text = JS_PATH.read_text(encoding="utf-8")
    cat_keys_js = [k for k in extract_top_level_string_keys(js_text) if k.isdigit()]
    cat_blocks = parse_js_category_blocks(js_text)

    js_uc_ids: set[str] = set()
    for m in RE_ID.finditer(js_text):
        x, y, z = m.group(1), m.group(2), m.group(3)
        uid = f"{x}.{y}.{z}"
        js_uc_ids.add(uid)

    js_subcats_by_cat: dict[str, set[str]] = defaultdict(set)
    for ck, block in cat_blocks.items():
        if not ck.isdigit():
            continue
        for m in RE_ID.finditer(block):
            x, y = m.group(1), m.group(2)
            js_subcats_by_cat[ck].add(f"{x}.{y}")

    cat_dir_by_num, ssot_uc_by_cat, ssot_subcats_by_cat = collect_ssot_categories()

    issues: list[str] = []

    ssot_all_ucs: set[str] = set()
    for s in ssot_uc_by_cat.values():
        ssot_all_ucs |= s

    for uid in sorted(js_uc_ids):
        if uid not in ssot_all_ucs:
            issues.append(
                f"(a) JS references UC id {uid!r} but no matching "
                f"content/cat-*/UC-{uid}.json sidecar exists."
            )

    for cat_num in sorted(cat_dir_by_num.keys()):
        key = str(cat_num)
        if key not in cat_keys_js:
            issues.append(
                f"(b) Content folder {cat_dir_by_num[cat_num].name} "
                f"(category {cat_num}) has no top-level entry "
                f'"{key}" in non-technical-view.js.'
            )

    for cat_num in sorted(cat_dir_by_num.keys()):
        key = str(cat_num)
        js_subs = js_subcats_by_cat.get(key, set())
        for xy in sorted(ssot_subcats_by_cat[cat_num]):
            if xy not in js_subs:
                issues.append(
                    f"(c) JSON SSOT has subcategory {xy} in "
                    f"{cat_dir_by_num[cat_num].name} but "
                    f'non-technical-view.js category "{key}" has no `id` under '
                    f'`areas` with prefix "{xy}." (no representative UC for this '
                    "subcategory)."
                )

    ssot_cat_nums = set(cat_dir_by_num.keys())
    for key in sorted(cat_keys_js, key=lambda x: int(x)):
        if key.isdigit() and int(key) not in ssot_cat_nums:
            issues.append(
                f'(d) non-technical-view.js has category "{key}" but there is no '
                f"matching content/cat-{int(key):02d}-*/ folder."
            )

    for k in cat_keys_js:
        if k.isdigit() and k not in cat_blocks:
            issues.append(
                f"(extra) Category key {k!r} listed but block not extracted (parser bug?)."
            )

    print("=== non-technical-view.js vs content/cat-*/ JSON SSOT audit ===\n")
    print(f"JS categories (numeric keys): {len([k for k in cat_keys_js if k.isdigit()])}")
    print(f"JS UC id references: {len(js_uc_ids)}")
    print(f"SSOT category folders (cat-NN-*): {len(cat_dir_by_num)}")
    print(f"SSOT UC sidecars total (unique): {len(ssot_all_ucs)}\n")

    if not issues:
        print("No issues found.")
        return 0

    print(f"Issues found: {len(issues)}\n")
    for line in issues:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
