#!/usr/bin/env python3
"""Audit INDEX.md, the SSOT ``CAT_GROUPS`` / ``SPLUNK_APPS`` registries
(``tools/build/enrichment.py``), and use-case markdown for consistency.

Imports the constants directly from the SSOT module rather than parsing
the legacy ``build.py`` source. Pre-P1-step-5c (before 2026-05-09) this
audit ran ``ast.parse`` on the repo-root ``build.py`` to avoid the
import-time side effects of that monolithic build script. After P1
step 5c retires the legacy ``build.py``, the SSOT module
``tools/build/enrichment.py`` is the only home of the registries and
the import is side-effect-free.

Run: python3 -m splunk_uc audit-repo-consistency
"""

from __future__ import annotations

import argparse
import glob
import os
import pathlib
import re
import sys
from typing import Any

# parents[3] resolves: repo_consistency.py -> audits/ -> splunk_uc/ ->
# src/ -> repo root. The legacy ``os.path.dirname(os.path.dirname(...))``
# chain assumed a one-level depth and is now wrong by three.
REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[3])
UC_DIR = os.path.join(REPO_ROOT, "use-cases")
INDEX_PATH = os.path.join(REPO_ROOT, "content", "INDEX.md")
INDEX_HTML = os.path.join(REPO_ROOT, "index.html")

# Ensure ``tools/`` is importable for both pip-installed and in-tree
# checkout invocations (CI runs from a fresh checkout without install).
_TOOLS_DIR = pathlib.Path(REPO_ROOT) / "tools"
if _TOOLS_DIR.is_dir() and str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

RE_CAT_HEADER = re.compile(r"^##\s+(\d+)\.\s+(.+)$")
RE_ICON = re.compile(r"^-\s+\*\*Icon:\*\*\s*(.+)$")
RE_STARTER = re.compile(r"^-\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+?)\s*\((\w+)(?:,\s*(.+?))?\)\s*$")
EXPECTED_CATS = set(range(1, 24))
REQUIRED_SPLUNK_APP_KEYS = ("name", "id", "url", "tas", "desc")


def parse_si_paths_keys(html_text: str) -> set[str]:
    for prefix in ("var SI_PATHS = ", "var SI_PATHS=", "var SI = ", "var SI="):
        start = html_text.find(prefix)
        if start != -1:
            break
    else:
        return set()
    brace = html_text.find("{", start)
    depth = 0
    i = brace
    while i < len(html_text):
        c = html_text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                block = html_text[brace : i + 1]
                return set(re.findall(r"(?m)^\s+(\w+)\s*:\s*['\"]", block))
        i += 1
    return set()


def parse_index() -> list[dict[str, Any]]:
    with open(INDEX_PATH, encoding="utf-8") as f:
        lines = f.readlines()
    categories: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_starters = False
    for line in lines:
        stripped = line.strip()
        m = RE_CAT_HEADER.match(stripped)
        if m:
            current = {"num": m.group(1), "name": m.group(2).strip(), "icon": None, "starters": []}
            categories.append(current)
            in_starters = False
            continue
        if current is None:
            continue
        m = RE_ICON.match(stripped)
        if m:
            current["icon"] = m.group(1).strip()
            in_starters = False
            continue
        if stripped == "- **Quick Start:**":
            in_starters = True
            continue
        if in_starters:
            m = RE_STARTER.match(stripped)
            if m:
                current["starters"].append(m.group(1))
            elif stripped and not stripped.startswith("-"):
                in_starters = False
    return categories


def extract_build_assignments() -> tuple[dict[str, list[int]], list[Any]]:
    """Return (CAT_GROUPS, SPLUNK_APPS) from the SSOT enrichment module.

    Per ADR-0008 every constant lives in exactly one place; the SSOT for
    these registries is ``tools/build/enrichment.py``. Importing the
    module is side-effect-free (no I/O at import time) so this is just
    as cheap as the previous ast-parsing approach but loses the
    cross-source-of-truth drift risk.
    """
    from build.enrichment import CAT_GROUPS, SPLUNK_APPS

    if not isinstance(CAT_GROUPS, dict):
        raise RuntimeError("tools/build/enrichment.py:CAT_GROUPS is not a dict")
    if not isinstance(SPLUNK_APPS, list):
        raise RuntimeError("tools/build/enrichment.py:SPLUNK_APPS is not a list")
    return CAT_GROUPS, SPLUNK_APPS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    issues: list[str] = []

    if not os.path.isfile(INDEX_PATH):
        issues.append(f"FATAL: Missing {INDEX_PATH}")
        for line in issues:
            print(line)
        return 1

    with open(INDEX_HTML, encoding="utf-8") as f:
        html = f.read()
    valid_icons = parse_si_paths_keys(html)
    if not valid_icons:
        issues.append("WARN: Could not parse SI_PATHS from index.html — icon checks skipped")

    categories = parse_index()
    seen_headers: dict[int, str] = {}
    for c in categories:
        n = int(c["num"])
        if n in seen_headers:
            issues.append(
                f"INDEX: Duplicate category header ## {n}. ({seen_headers[n]!r} vs {c['name']!r})"
            )
        else:
            seen_headers[n] = str(c["name"])

    for n in EXPECTED_CATS:
        if n not in seen_headers:
            issues.append(f"INDEX: Missing category header for {n} (expected ## {n}. ...)")

    extra = set(seen_headers.keys()) - EXPECTED_CATS
    for n in sorted(extra):
        issues.append(f"INDEX: Unexpected category number {n} in INDEX.md (expected 1–23 only)")  # noqa: RUF001

    for c in categories:
        n = int(c["num"])
        pat = os.path.join(UC_DIR, f"cat-{n:02d}-*.md")
        matches = sorted(glob.glob(pat))
        if not matches:
            issues.append(
                f"INDEX: Category {n} ({c['name']!r}) has no matching file use-cases/cat-{n:02d}-*.md"
            )
        elif len(matches) > 1:
            issues.append(f"INDEX: Category {n} has multiple cat-{n:02d}-*.md files: {matches!r}")

        ic = c.get("icon")
        if isinstance(ic, str) and valid_icons and ic not in valid_icons:
            issues.append(f"INDEX: Category {n} Icon {ic!r} is not a key in index.html SI_PATHS")

        cat_file = matches[0] if len(matches) >= 1 else None
        if cat_file and os.path.isfile(cat_file):
            with open(cat_file, encoding="utf-8") as cf:
                body = cf.read()
            for sid in c["starters"]:
                token = f"UC-{sid}"
                if token not in body:
                    issues.append(
                        f"INDEX: Quick Start UC {token} for category {n} not found in {os.path.basename(cat_file)}"
                    )

    cat_groups: dict[str, list[int]] | None
    splunk_apps: list[Any] | None
    try:
        cat_groups, splunk_apps = extract_build_assignments()
    except Exception as e:
        issues.append(f"tools/build/enrichment.py: Failed to import CAT_GROUPS/SPLUNK_APPS — {e}")
        cat_groups, splunk_apps = None, None

    if cat_groups is not None and splunk_apps is not None:
        all_in_groups: list[int] = []
        for _gname, ids in cat_groups.items():
            for x in ids:
                all_in_groups.append(x)
        counts: dict[int, int] = {}
        for x in all_in_groups:
            counts[x] = counts.get(x, 0) + 1
        for n in EXPECTED_CATS:
            if n not in counts:
                issues.append(f"CAT_GROUPS: Category {n} is not in any group")
            elif counts[n] > 1:
                issues.append(
                    f"CAT_GROUPS: Category {n} appears {counts[n]} times (must be exactly once)"
                )
        for n in counts:
            if n not in EXPECTED_CATS:
                issues.append(f"CAT_GROUPS: Unexpected category id {n} (expected 1–23 only)")  # noqa: RUF001
        for gname, ids in cat_groups.items():
            for x in ids:
                if x not in EXPECTED_CATS:
                    issues.append(f"CAT_GROUPS: Group {gname!r} contains invalid category {x}")

        cat_ids_in_groups = set(all_in_groups)

        cat_files: list[str] = []
        for fn in sorted(os.listdir(UC_DIR)):
            if fn.startswith("cat-") and fn.endswith(".md") and fn != "cat-00-preamble.md":
                cat_files.append(os.path.join(UC_DIR, fn))

        for path in cat_files:
            base = os.path.basename(path)
            m = re.match(r"^cat-(\d{2})-", base)
            if not m:
                issues.append(f"cat file: Unexpected name pattern (expected cat-NN-*.md): {base}")
                continue
            num = int(m.group(1))
            if num not in cat_ids_in_groups:
                issues.append(
                    f"CAT_GROUPS: File {base} implies category {num}, but {num} is not in CAT_GROUPS union"
                )

        for path in cat_files:
            base = os.path.basename(path)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for mm in re.finditer(r"UC-(\d+)\.(\d+)\.(\d+)", text):
                uc_cat = int(mm.group(1))
                if uc_cat not in EXPECTED_CATS:
                    issues.append(
                        f"cat-*.md: UC-{uc_cat}.{mm.group(2)}.{mm.group(3)} in {base} — "
                        f"category {uc_cat} is not valid (1–23)"  # noqa: RUF001
                    )
                elif uc_cat not in cat_ids_in_groups:
                    issues.append(
                        f"cat-*.md: UC-{uc_cat}.{mm.group(2)}.{mm.group(3)} in {base} — "
                        f"category {uc_cat} not in CAT_GROUPS"
                    )

        seen_ids: dict[object, list[str]] = {}
        for i, app in enumerate(splunk_apps):
            if not isinstance(app, dict):
                issues.append(f"SPLUNK_APPS[{i}]: entry is not a dict")
                continue
            for key in REQUIRED_SPLUNK_APP_KEYS:
                if key not in app:
                    issues.append(
                        f"SPLUNK_APPS[{i}] ({app.get('name', '?')!r}): missing required field {key!r}"
                    )
            aid = app.get("id")
            if aid is not None:
                seen_ids.setdefault(aid, []).append(str(app.get("name", "?")))
        for aid, names in seen_ids.items():
            if len(names) > 1:
                issues.append(f"SPLUNK_APPS: duplicate app id {aid}: {names!r}")

    print("Repository consistency audit")
    print("=" * 60)
    if not issues:
        print("No issues found.")
        return 0
    print(f"Found {len(issues)} issue(s):\n")
    for line in issues:
        print(line)
    return 2


if __name__ == "__main__":
    sys.exit(main())
