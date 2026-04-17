#!/usr/bin/env python3
"""Repair broken reference URLs on `- **References:**` lines.

Two classes of fixes:

1. Bogus Splunkbase app links previously inserted by `fill_references.py`.
   Small numeric IDs (Windows Event IDs 129, 134, 4624…) were mistaken for
   Splunkbase app IDs.  We delete every `[label](https://splunkbase...)`
   link whose ID is in a known-404 deny-list, then collapse empty lists.

2. MITRE ATT&CK URL format drift: `/techniques/T1059.001/` → `/techniques/
   T1059/001/` (the canonical format introduced by ATT&CK v12).

The script preserves idempotency: running it twice yields no further
changes.
"""

from __future__ import annotations

import argparse
import os
import re
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
UC_DIR = os.path.join(REPO_ROOT, "use-cases")

# Splunkbase app IDs verified as 404 on 2026-04-16.  Any reference link
# pointing to one of these is stale and must be removed.
KNOWN_404_SPLUNKBASE: set[int] = {
    129, 134, 140, 141, 142, 302, 303, 429, 776,
    2004, 2005, 2006, 2026, 3002,
    4624, 4733, 4769, 4893,
    10016, 12802,
}

MITRE_SUBTECH_RE = re.compile(
    r"https?://attack\.mitre\.org/techniques/T(\d{4})\.(\d{3})(/?)",
    re.IGNORECASE,
)

REFERENCES_LINE_RE = re.compile(r"^(\s*-\s*\*\*References:\*\*\s*)(.+)$", re.MULTILINE)

# A single markdown link on a References line, e.g. `[label](URL)`
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

FALLBACK_LINK = "[Splunk Lantern — use case library](https://lantern.splunk.com/)"


def fix_mitre_urls(text: str) -> tuple[str, int]:
    """Convert `/techniques/TXXXX.YYY(/)` → `/techniques/TXXXX/YYY/`."""

    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"https://attack.mitre.org/techniques/T{m.group(1)}/{m.group(2)}/"

    new = MITRE_SUBTECH_RE.sub(repl, text)
    return new, count


def _clean_refs_line(raw: str) -> tuple[str, int]:
    """Strip dead Splunkbase links from a single `- **References:** ...` line
    value.  Returns (new_value, removed_count).
    """
    removed = 0
    kept: List[str] = []

    # We split by comma carefully: markdown links do not contain commas
    # inside `[...]` or `(...)` in this codebase, so a simple split works
    # provided we trim whitespace.
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    for p in parts:
        m = LINK_RE.fullmatch(p)
        if m and "splunkbase.splunk.com/app/" in m.group(2):
            # Extract the numeric ID
            id_match = re.search(r"/app/(\d+)", m.group(2))
            if id_match and int(id_match.group(1)) in KNOWN_404_SPLUNKBASE:
                removed += 1
                continue
        kept.append(p)

    if not kept:
        kept = [FALLBACK_LINK]
    return ", ".join(kept), removed


def fix_splunkbase_links(text: str) -> tuple[str, int, int]:
    total_removed = 0
    lines_touched = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal total_removed, lines_touched
        prefix, body = m.group(1), m.group(2)
        new_body, removed = _clean_refs_line(body)
        if removed:
            total_removed += removed
            lines_touched += 1
            return prefix + new_body
        return m.group(0)

    new = REFERENCES_LINE_RE.sub(repl, text)
    return new, total_removed, lines_touched


def process_file(path: str, write: bool) -> tuple[int, int, int]:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    text, mitre_fixed = fix_mitre_urls(original)
    text, removed, lines_touched = fix_splunkbase_links(text)
    if write and text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return mitre_fixed, removed, lines_touched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    grand_mitre = 0
    grand_removed = 0
    grand_lines = 0
    for path in cat_files:
        mitre, removed, lines = process_file(path, args.write)
        if mitre or removed:
            print(
                f"  {os.path.basename(path):48}  "
                f"mitre:+{mitre:3}  dead-splunkbase:-{removed:3}  lines:{lines:3}"
            )
        grand_mitre += mitre
        grand_removed += removed
        grand_lines += lines
    print("-" * 70)
    print(
        f"MITRE URLs rewritten: {grand_mitre}; "
        f"dead Splunkbase links removed: {grand_removed}; "
        f"reference lines touched: {grand_lines}"
    )
    if not args.write:
        print("(dry run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
