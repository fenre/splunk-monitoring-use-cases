#!/usr/bin/env python3
"""
Audit non-technical-view.js vs use-cases/cat-*.md UC and category coverage.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JS_PATH = REPO / "non-technical-view.js"
USE_CASES = REPO / "use-cases"

# UC lines: ### UC-X.Y.Z
RE_UC_HEADER = re.compile(r"^###\s+UC-(\d+)\.(\d+)\.(\d+)\b", re.MULTILINE)
# Subcategory: ## X.Y
RE_SUBCAT = re.compile(r"^##\s+(\d+)\.(\d+)\s", re.MULTILINE)
RE_ID = re.compile(r'id:\s*"(\d+)\.(\d+)\.(\d+)"')


def extract_top_level_string_keys(js_text: str) -> list[str]:
    """Find quoted string keys immediately under window.NON_TECHNICAL = { ... } at depth 1."""
    m = re.search(r"window\.NON_TECHNICAL\s*=\s*\{", js_text)
    if not m:
        raise ValueError("window.NON_TECHNICAL = { not found")
    i = m.end() - 1  # position at '{'
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
    """Return map category_key -> substring of that category's object."""
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


def main() -> None:
    js_text = JS_PATH.read_text(encoding="utf-8")
    cat_keys_js = [k for k in extract_top_level_string_keys(js_text) if k.isdigit()]
    cat_blocks = parse_js_category_blocks(js_text)

    js_uc_ids: set[str] = set()
    for m in RE_ID.finditer(js_text):
        x, y, z = m.group(1), m.group(2), m.group(3)
        uid = f"{x}.{y}.{z}"
        js_uc_ids.add(uid)

    # Subcategory prefixes X.Y covered in JS per category (from ids in that category's block only)
    js_subcats_by_cat: dict[str, set[str]] = defaultdict(set)
    for ck, block in cat_blocks.items():
        if not ck.isdigit():
            continue
        for m in RE_ID.finditer(block):
            x, y = m.group(1), m.group(2)
            js_subcats_by_cat[ck].add(f"{x}.{y}")

    md_files = sorted(USE_CASES.glob("cat-*.md"))
    md_by_cat: dict[int, Path] = {}

    for p in md_files:
        rm = re.match(r"^cat-(\d{2})-.+\.md$", p.name)
        if rm:
            num = int(rm.group(1))
            if num != 0:
                md_by_cat[num] = p

    md_uc_by_cat: dict[int, set[str]] = defaultdict(set)
    md_subcats_by_cat: dict[int, set[str]] = defaultdict(set)

    for cat_num, path in sorted(md_by_cat.items()):
        text = path.read_text(encoding="utf-8")
        for a, b, c in RE_UC_HEADER.findall(text):
            uid = f"{a}.{b}.{c}"
            md_uc_by_cat[cat_num].add(uid)
        for a, b in RE_SUBCAT.findall(text):
            if int(a) != cat_num:
                continue
            md_subcats_by_cat[cat_num].add(f"{a}.{b}")

    issues: list[str] = []

    md_all_ucs: set[str] = set()
    for s in md_uc_by_cat.values():
        md_all_ucs |= s

    for uid in sorted(js_uc_ids):
        if uid not in md_all_ucs:
            issues.append(
                f"(a) JS references UC id {uid!r} but no matching ### UC-{uid} header was found in any cat-*.md file."
            )

    for cat_num in sorted(md_by_cat.keys()):
        key = str(cat_num)
        if key not in cat_keys_js:
            issues.append(
                f"(b) Markdown category file {md_by_cat[cat_num].name} (category {cat_num}) has no top-level entry "
                f'"{key}" in non-technical-view.js.'
            )

    for cat_num in sorted(md_by_cat.keys()):
        key = str(cat_num)
        js_subs = js_subcats_by_cat.get(key, set())
        for xy in sorted(md_subcats_by_cat[cat_num]):
            if xy not in js_subs:
                issues.append(
                    f"(c) Markdown has subcategory ## {xy} in {md_by_cat[cat_num].name} but non-technical-view.js "
                    f'category "{key}" has no `id` under `areas` with prefix "{xy}." (no representative UC for this subcategory).'
                )

    md_cat_nums = set(md_by_cat.keys())
    for key in sorted(cat_keys_js, key=lambda x: int(x)):
        if key.isdigit() and int(key) not in md_cat_nums:
            issues.append(
                f'(d) non-technical-view.js has category "{key}" but there is no matching use-cases/cat-{int(key):02d}-*.md file.'
            )

    for k in cat_keys_js:
        if k.isdigit() and k not in cat_blocks:
            issues.append(f"(extra) Category key {k!r} listed but block not extracted (parser bug?).")

    print("=== non-technical-view.js vs use-cases/cat-*.md audit ===\n")
    print(f"JS categories (numeric keys): {len([k for k in cat_keys_js if k.isdigit()])}")
    print(f"JS UC id references: {len(js_uc_ids)}")
    print(f"Markdown category files (cat-NN): {len(md_by_cat)}")
    print(f"Markdown UC headers total (unique): {len(md_all_ucs)}\n")

    if not issues:
        print("No issues found.")
    else:
        print(f"Issues found: {len(issues)}\n")
        for line in issues:
            print(line)


if __name__ == "__main__":
    main()
