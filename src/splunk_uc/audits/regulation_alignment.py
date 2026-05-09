#!/usr/bin/env python3
"""Lint compliance[].regulation against data/regulations.json (id, shortName, aliases).

Unknown labels (no case-insensitive match) → stderr, exit 1.
Optional --fix-case rewrites matched labels to the canonical framework id.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def _lower_to_canon(regs_path: Path) -> dict[str, str]:
    data = json.loads(regs_path.read_text(encoding="utf-8"))
    m: dict[str, str] = {}
    for fw in data.get("frameworks", []):
        canon: str = fw["id"]
        for lab in (canon, fw.get("shortName"), *fw.get("aliases", [])):
            if isinstance(lab, str) and lab.strip():
                m[lab.casefold()] = canon
    return m


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--fix-case",
        action="store_true",
        help="set regulation to canonical id when it matches id/shortName/alias but differs",
    )
    args = ap.parse_args(argv)
    reg = _lower_to_canon(REPO / "data" / "regulations.json")
    unknown: list[str] = []
    for path in sorted((REPO / "content").glob("cat-*/UC-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        com = doc.get("compliance")
        if not isinstance(com, list):
            continue
        dirty = False
        rel = path.relative_to(REPO)
        for i, row in enumerate(com):
            if not isinstance(row, dict):
                continue
            val = row.get("regulation")
            if not isinstance(val, str) or not val.strip():
                continue
            key = val.casefold()
            if key not in reg:
                unknown.append(f"{rel} compliance[{i}].regulation unknown: {val!r}")
                continue
            canon = reg[key]
            if args.fix_case and val != canon:
                row["regulation"] = canon
                dirty = True
        if dirty:
            path.write_text(
                json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
    for line in unknown:
        print(line, file=sys.stderr)
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
