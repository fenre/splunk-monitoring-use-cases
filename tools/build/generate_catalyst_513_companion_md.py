#!/usr/bin/env python3
"""Generate UC-5.13.*.md companion files from JSON using migrate_to_per_uc rendering."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CATALYST_DIR = REPO_ROOT / "content" / "cat-05-network-infrastructure"

# Reuse the canonical markdown renderer (identical to full-tree migration)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_to_per_uc import _render_uc_markdown  # noqa: E402


def main() -> int:
    pattern = "UC-5.13.*.json"
    paths = sorted(CATALYST_DIR.glob(pattern))
    if not paths:
        print(f"No files matching {pattern} under {CATALYST_DIR}", file=sys.stderr)
        return 1

    for json_path in paths:
        with json_path.open(encoding="utf-8") as f:
            data: dict = json.load(f)
        if not isinstance(data, dict):
            print(f"SKIP (not an object): {json_path.name}", file=sys.stderr)
            continue
        md_text = _render_uc_markdown(data)
        md_path = json_path.with_suffix(".md")
        md_path.write_text(md_text, encoding="utf-8")

    # Verify count of UC-5.13.*.md in directory
    md_files = sorted(CATALYST_DIR.glob("UC-5.13.*.md"))
    n = len(md_files)
    print(f"Wrote {len(paths)} companion .md file(s) from JSON.")
    print(f"UC-5.13.*.md count under {CATALYST_DIR.relative_to(REPO_ROOT)}: {n}")
    if n != len(paths):
        print(
            f"WARNING: JSON count ({len(paths)}) != .md count ({n})",
            file=sys.stderr,
        )
        return 1
    if n != 78:
        print(f"ERROR: expected 78 .md files, got {n}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
