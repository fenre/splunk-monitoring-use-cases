#!/usr/bin/env python3
"""
Normalize common non-CIM IP field names to CIM-style src/dest in use-cases markdown.

- All_Traffic.src_ip / All_Traffic.dest_ip -> All_Traffic.src / All_Traffic.dest
- All_Sessions.*_ip -> All_Sessions.src / All_Sessions.dest
- Standalone src_ip / dest_ip -> src / dest (skips connection.src_ip / connection.dest_ip)

After running, manually verify BY clauses: if both All_Traffic.dest and All_Traffic.dest_ip
were present, you may end up with duplicate All_Traffic.dest on adjacent lines — merge
to a single field (see git history for examples).

Run from repo root: python3 scripts/normalize_cim_fields.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USE_CASES = ROOT / "use-cases"

DM_PREFIX = [
    ("All_Traffic.dest_ip", "All_Traffic.dest"),
    ("All_Traffic.src_ip", "All_Traffic.src"),
    ("All_Sessions.dest_ip", "All_Sessions.dest"),
    ("All_Sessions.src_ip", "All_Sessions.src"),
]


def normalize_block(text: str) -> str:
    for old, new in DM_PREFIX:
        text = text.replace(old, new)
    text = re.sub(r"(?<!connection\.)\bdest_ip\b", "dest", text)
    text = re.sub(r"(?<!connection\.)\bsrc_ip\b", "src", text)
    return text


def main() -> None:
    files = sorted(USE_CASES.glob("cat-*.md"))
    changed = 0
    for path in files:
        raw = path.read_text(encoding="utf-8")
        new = normalize_block(raw)
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed += 1
            print(f"updated {path.name}")
    print(f"Done. {changed} files modified.")


if __name__ == "__main__":
    main()
