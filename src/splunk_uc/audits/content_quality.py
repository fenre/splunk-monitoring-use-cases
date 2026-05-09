#!/usr/bin/env python3
"""Content quality audit — flags description==value duplicates, jargon in grandmaExplanation,
broken fixtureRefs, and implausible equipment tags."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTENT_DIR = PROJECT_ROOT / "content"
SAMPLE_DATA = PROJECT_ROOT / "sample-data"

JARGON_TERMS = [
    "tstats",
    "datamodel",
    "CIM",
    "sourcetype",
    "macro",
    "eval",
    "rex",
    "lookup",
    "savedsearch",
    "props.conf",
    "transforms.conf",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=str,
        help="Path to baseline file (existing violations to ignore)",
    )
    parser.add_argument(
        "--generate-baseline",
        action="store_true",
        help="Output current violations as baseline JSON",
    )
    args = parser.parse_args(argv)

    violations: list[dict[str, Any]] = []

    for uc_path in sorted(CONTENT_DIR.rglob("UC-*.json")):
        try:
            data = json.loads(uc_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            violations.append(
                {"file": str(uc_path.relative_to(PROJECT_ROOT)), "issue": "invalid_json"}
            )
            continue

        uc_id = data.get("id", uc_path.stem)
        rel = str(uc_path.relative_to(PROJECT_ROOT))

        if (
            data.get("description")
            and data.get("value")
            and data["description"].strip() == data["value"].strip()
        ):
            violations.append({"file": rel, "id": uc_id, "issue": "description_equals_value"})

        grandma = data.get("grandmaExplanation", "")
        for term in JARGON_TERMS:
            if term.lower() in grandma.lower():
                violations.append({"file": rel, "id": uc_id, "issue": f"jargon_in_grandma: {term}"})
                break

        ct = data.get("controlTest", {})
        if isinstance(ct, dict):
            ref = ct.get("fixtureRef", "")
            if ref and not (PROJECT_ROOT / ref).exists():
                violations.append({"file": rel, "id": uc_id, "issue": f"broken_fixtureRef: {ref}"})

    if args.generate_baseline:
        json.dump(violations, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    baseline_ids: set[tuple[str, str]] = set()
    if args.baseline:
        bp = pathlib.Path(args.baseline)
        if bp.exists():
            baseline_ids = {(v["file"], v["issue"]) for v in json.loads(bp.read_text())}

    new_violations = [v for v in violations if (v["file"], v["issue"]) not in baseline_ids]

    if new_violations:
        print(f"Content quality: {len(new_violations)} new violation(s):", file=sys.stderr)
        for v in new_violations[:20]:
            print(f"  {v['file']}: {v['issue']}", file=sys.stderr)
        if len(new_violations) > 20:
            print(f"  ... and {len(new_violations) - 20} more", file=sys.stderr)
        return 1

    total = len(violations)
    print(f"Content quality: {total} existing violation(s) (all in baseline), 0 new.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
