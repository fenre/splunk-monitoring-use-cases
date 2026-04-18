#!/usr/bin/env python3
"""Repair `Known false positives:` fields mangled by YAML import.

Replaces ESCU-import artefacts where the YAML block-scalar indicator
`known_false_positives: |` collapsed to a single `|` character. The
replacement text is deliberately conservative — it tells the reader
that no FPs are documented in the upstream ESCU detection and nudges
them to consult the linked references for vendor guidance.

Idempotent; use `--dry-run` to preview counts before writing.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"

RE_FP_PIPE_STUB = re.compile(
    r"^(?P<prefix>-[ \t]*\*\*Known false positives:\*\*[ \t]*)\|[ \t]*$",
    re.MULTILINE,
)

REPLACEMENT = (
    "None explicitly documented by the upstream ESCU detection — review"
    " alerts in business context before suppressing, and consult the"
    " linked references for vendor guidance."
)


def process_file(path: pathlib.Path, write: bool) -> int:
    original = path.read_text(encoding="utf-8")
    fixes = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal fixes
        fixes += 1
        return f"{match.group('prefix')}{REPLACEMENT}"

    rewritten = RE_FP_PIPE_STUB.sub(_repl, original)
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
            action = "would repair" if args.dry_run else "repaired"
            print(f"  {action} {md.name}: {fixes} pipe stub(s)")
    print(
        f"\n{'(dry-run) ' if args.dry_run else ''}"
        f"Total Known-FP pipe stubs repaired: {total}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
