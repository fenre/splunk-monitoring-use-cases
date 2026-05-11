#!/usr/bin/env python3
"""Fix Splunk_TA_/Splunk_SA_ package-name typos where the convention
between the prefix and the vendor uses a dash (`-`) instead of the
canonical underscore (`_`).

Splunkbase TA package names follow the strict pattern
``Splunk_TA_<vendor>_<product>`` or ``Splunk_TA_<vendor>``. Any dashes
inside this slug are typos (the prefix is always `_TA_`).

The script normalises to underscores INSIDE the Splunk_TA_/Splunk_SA_
slug. It does NOT touch standalone vendor names with dashes elsewhere.
Pass --write to apply.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

# Match Splunk_TA_/Splunk_SA_ identifiers that contain dashes
TYPO_RE = re.compile(
    r"\b(Splunk_TA_|Splunk_SA_)([A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)+)\b"
)


def normalise(match: re.Match) -> str:
    prefix = match.group(1)
    rest = match.group(2)
    return prefix + rest.replace("-", "_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fixed_files = 0
    total = 0
    by_replacement: dict[str, int] = {}
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        changed = False
        for fld in (
            "app",
            "dataSources",
            "implementation",
            "detailedImplementation",
            "description",
            "value",
            "spl",
            "cimSpl",
            "knownFalsePositives",
            "visualization",
            "exclusions",
            "evidence",
            "schema",
            "dataModelAcceleration",
        ):
            v = d.get(fld)
            if not isinstance(v, str):
                continue
            new_v, n = TYPO_RE.subn(normalise, v)
            if n:
                d[fld] = new_v
                changed = True
                total += n
                for m in TYPO_RE.finditer(v):
                    original = m.group(0)
                    fixed = TYPO_RE.sub(normalise, original)
                    by_replacement[f"{original} → {fixed}"] = by_replacement.get(
                        f"{original} → {fixed}", 0
                    ) + 1
        if changed:
            fixed_files += 1
            if args.write:
                p.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

    print(f"Files fixed: {fixed_files}, total replacements: {total}")
    for k, n in sorted(by_replacement.items(), key=lambda x: -x[1])[:30]:
        print(f"  {n:4} {k}")
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
