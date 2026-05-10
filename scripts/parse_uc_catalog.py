#!/usr/bin/env python3
"""Emit ``manifest-all.json`` from the JSON SSOT (``content/cat-*/UC-*.json``).

Walks the SSOT sidecars and produces a flat manifest of all use cases with
``uc_id``, ``title``, source-file pointer, category number, and the default
``log_family`` from ``config/uc_to_log_family.json``.

Usage::

  python3 scripts/parse_uc_catalog.py --output eventgen_data/manifest-all.json
  python3 scripts/parse_uc_catalog.py  # writes to stdout

The legacy ``use-cases/cat-*.md`` markdown corpus has been retired; this
script now reads exclusively from ``content/`` (the SSOT).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

CAT_DIR = re.compile(r"^cat-(\d+)-.+$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def category_from_dirname(name: str) -> int | None:
    m = CAT_DIR.match(name)
    if not m:
        return None
    return int(m.group(1))


def load_family_map(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("category_to_family", {})


def parse_uc_sidecar(path: Path, category: int, default_family: str) -> dict | None:
    try:
        with path.open(encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    uc_id = payload.get("id") or path.stem.removeprefix("UC-")
    title = payload.get("title") or ""
    return {
        "uc_id": uc_id,
        "title": title.strip(),
        "catalog_category": category,
        "source_file": str(path.relative_to(repo_root())),
        "log_family": default_family,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build manifest-all.json from content/cat-*/UC-*.json (JSON SSOT)."
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=repo_root() / "content",
        help="Path to the SSOT content directory (default: <repo>/content).",
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

    for cat_dir in sorted(args.content_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat = category_from_dirname(cat_dir.name)
        if cat is None:
            continue
        default_family = family_map.get(str(cat), "web")
        for sidecar in sorted(cat_dir.glob("UC-*.json")):
            row = parse_uc_sidecar(sidecar, cat, default_family)
            if row is not None:
                all_rows.append(row)

    all_rows.sort(key=lambda r: r["uc_id"])

    manifest = {
        "description": "Auto-generated list of all use cases from content/cat-*/UC-*.json (JSON SSOT)",
        "generated_at": datetime.now(UTC).isoformat(),
        "uc_count": len(all_rows),
        "use_cases": all_rows,
    }

    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    if args.check and len(all_rows) < 1:
        print("ERROR: no use cases parsed", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
