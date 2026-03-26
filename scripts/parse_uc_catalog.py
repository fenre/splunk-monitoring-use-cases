#!/usr/bin/env python3
"""
Parse all use case headings from use-cases/cat-*.md and emit manifest-all.json
with uc_id, title, source file, category number, and default log_family from
config/uc_to_log_family.json.

Usage:
  python3 scripts/parse_uc_catalog.py --output eventgen_data/manifest-all.json

  python3 scripts/parse_uc_catalog.py  # writes to stdout

Excludes: cat-00-preamble.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

UC_HEADING = re.compile(r"^#{3,4}\s+UC-(\d+\.\d+\.\d+)\s*[·•]\s*(.+)$")
CAT_FILE = re.compile(r"^cat-(\d+)-.+\.md$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def category_from_filename(name: str) -> int | None:
    m = CAT_FILE.match(name)
    if not m:
        return None
    return int(m.group(1))


def load_family_map(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("category_to_family", {})


def parse_uc_file(path: Path, category: int, default_family: str) -> list[dict]:
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = UC_HEADING.match(line.strip())
        if not m:
            continue
        uc_id, title = m.group(1), m.group(2).strip()
        out.append(
            {
                "uc_id": uc_id,
                "title": title,
                "catalog_category": category,
                "source_file": str(path.relative_to(repo_root())),
                "log_family": default_family,
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build manifest-all.json from cat-*.md")
    parser.add_argument(
        "--use-cases-dir",
        type=Path,
        default=repo_root() / "use-cases",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=repo_root() / "config" / "uc_to_log_family.json",
    )
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 only if output is valid JSON with at least one use case",
    )
    args = parser.parse_args()

    family_map = load_family_map(args.config)
    all_rows: list[dict] = []

    for md in sorted(args.use_cases_dir.glob("cat-*.md")):
        if md.name == "cat-00-preamble.md":
            continue
        cat = category_from_filename(md.name)
        if cat is None:
            continue
        key = str(cat)
        default_family = family_map.get(key, "web")
        all_rows.extend(parse_uc_file(md, cat, default_family))

    all_rows.sort(key=lambda r: r["uc_id"])

    manifest = {
        "description": "Auto-generated list of all use cases from UC headings in use-cases/cat-*.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "uc_count": len(all_rows),
        "use_cases": all_rows,
    }

    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")

    if not args.output:
        sys.stdout.write(text)

    if args.check and len(all_rows) < 1:
        print("ERROR: no use cases parsed", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
