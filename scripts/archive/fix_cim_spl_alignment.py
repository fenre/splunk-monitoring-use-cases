#!/usr/bin/env python3
"""Normalise non-canonical CIM model spellings in `CIM Models:` lines.

Rewrites every occurrence of spellings such as `Network Traffic`,
`Ticket Management`, or `Intrusion Detection` (space-separated) to the
underscore-separated form used by CIM datamodel identifiers — which is
what `tstats` and `pivot` require.

Idempotent; use `--dry-run` to preview counts without touching the tree.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
USE_CASES = REPO / "use-cases"

RE_CIM_MODELS = re.compile(
    r"^(?P<prefix>-[ \t]*\*\*CIM Models:\*\*[ \t]*)(?P<body>[^\n]*)$",
    re.MULTILINE,
)

TOKEN_NORMALISATION = {
    "Network Traffic": "Network_Traffic",
    "Ticket Management": "Ticket_Management",
    "Intrusion Detection": "Intrusion_Detection",
    "Network Sessions": "Network_Sessions",
    "Network Resolution": "Network_Resolution",
    "Compute Inventory": "Compute_Inventory",
}


def _rewrite_value(body: str) -> tuple[str, int]:
    new = body
    replacements = 0
    for bad, good in TOKEN_NORMALISATION.items():
        pattern = re.compile(rf"\b{re.escape(bad)}\b")
        new, n = pattern.subn(good, new)
        replacements += n
    return new, replacements


def process_file(path: pathlib.Path, write: bool) -> int:
    original = path.read_text(encoding="utf-8")
    fixes = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal fixes
        body = match.group("body")
        new_body, n = _rewrite_value(body)
        if n == 0:
            return match.group(0)
        fixes += n
        return f"{match.group('prefix')}{new_body}"

    rewritten = RE_CIM_MODELS.sub(_repl, original)
    if fixes and write:
        path.write_text(rewritten, encoding="utf-8")
    return fixes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts per file without saving.",
    )
    args = parser.parse_args()

    total = 0
    for md in sorted(USE_CASES.glob("cat-*.md")):
        fixes = process_file(md, write=not args.dry_run)
        if fixes:
            total += fixes
            action = "would normalise" if args.dry_run else "normalised"
            print(f"  {action} {md.name}: {fixes} token(s)")
    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}"
        f"Total CIM model token normalisations: {total}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
