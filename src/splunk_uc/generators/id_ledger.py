#!/usr/bin/env python3
"""Generate or verify ``data/id-ledger.json`` from the live catalogue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from splunk_uc.id_ledger import (
    LEDGER_PATH,
    build_ledger_document,
    catalogue_index,
    load_ledger,
    validate_ledger_revision_monotonicity,
)


def _canonical_json(doc: dict) -> str:
    # Entries are already emitted in sorted id order; avoid sort_keys on the
    # full document so entry object key order stays human-readable.
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify the append-only UC identifier ledger."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute the ledger and fail if data/id-ledger.json would change.",
    )
    args = parser.parse_args(argv)

    catalogue = catalogue_index()
    previous = load_ledger() if LEDGER_PATH.is_file() else None
    generated = build_ledger_document(catalogue=catalogue, previous=previous)
    revision_issues = validate_ledger_revision_monotonicity(previous, generated)
    rendered = _canonical_json(generated)

    if args.check:
        if not LEDGER_PATH.is_file():
            print(f"FAIL: missing {LEDGER_PATH.relative_to(Path.cwd())}", file=sys.stderr)
            return 1
        if revision_issues:
            print("FAIL: fingerprint revision history would be shortened:", file=sys.stderr)
            for issue in revision_issues:
                print(f"  - {issue}", file=sys.stderr)
            return 1
        on_disk = LEDGER_PATH.read_text(encoding="utf-8")
        if on_disk != rendered:
            print(
                "FAIL: data/id-ledger.json is stale — run "
                "PYTHONPATH=src python3 -m splunk_uc generate-id-ledger",
                file=sys.stderr,
            )
            return 1
        print(f"PASS: id-ledger OK ({generated['entryCount']} entries)")
        return 0

    if revision_issues:
        print("FAIL: fingerprint revision history would be shortened:", file=sys.stderr)
        for issue in revision_issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {LEDGER_PATH} ({generated['entryCount']} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
