#!/usr/bin/env python3
"""Maintainer helper for appending vendor changelog entries safely.

Handles ID generation, deterministic re-sort, and ``generated`` date stamping.
The hand-edited JSON file remains the v1 source of truth; this tool reduces
authoring mistakes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from splunk_uc.audits.vendor_changelog import (
    VENDOR_CHANGELOG_DIR,
    VendorChangelogError,
    load_vendor_changelog,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_ENTRY_ID_RE = re.compile(r"^([A-Z]+)-(\d{4})-(\d{3})$")


def _vendor_path(vendor: str) -> Path:
    return VENDOR_CHANGELOG_DIR / f"{vendor}.json"


def _next_entry_id(vendor: str, entries: list[dict[str, Any]], year: int) -> str:
    prefix = vendor.upper().replace("-", "_")
    if prefix == "CISCO":
        prefix = "CISCO"
    max_seq = 0
    for entry in entries:
        entry_id = str(entry.get("id", ""))
        match = _ENTRY_ID_RE.match(entry_id)
        if not match:
            continue
        entry_prefix, entry_year, seq = match.groups()
        if entry_prefix == prefix and int(entry_year) == year:
            max_seq = max(max_seq, int(seq))
    return f"{prefix}-{year}-{max_seq + 1:03d}"


def _sort_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def _key(item: dict[str, Any]) -> tuple[int, str]:
        release_date = str(item.get("release_date", ""))
        try:
            ordinal = date.fromisoformat(release_date).toordinal()
        except ValueError:
            ordinal = 0
        return (-ordinal, str(item.get("id", "")))

    return sorted(entries, key=_key)


def _build_entry_from_args(args: argparse.Namespace, entry_id: str) -> dict[str, Any]:
    fields_renamed: list[dict[str, str]] = []
    if args.rename_from and args.rename_to:
        fields_renamed.append({"from": args.rename_from, "to": args.rename_to})

    today = date.today().isoformat()
    return {
        "id": entry_id,
        "product": args.product,
        "product_display": args.product_display or args.product,
        "release": args.release,
        "release_date": args.release_date,
        "change_kind": args.change_kind,
        "summary": args.summary,
        "details": args.details,
        "fields_added": list(args.fields_added or []),
        "fields_removed": list(args.fields_removed or []),
        "fields_renamed": fields_renamed,
        "fields_deprecated": list(args.fields_deprecated or []),
        "spl_impact": args.spl_impact,
        "affected_uc_categories": list(args.categories or []),
        "source_url": args.source_url,
        "source_kind": args.source_kind,
        "severity": args.severity,
        "added_by": args.added_by,
        "added_date": today,
    }


def add_entry(vendor: str, entry: dict[str, Any], *, dry_run: bool = False) -> Path:
    path = _vendor_path(vendor)
    if not path.is_file():
        raise VendorChangelogError(f"vendor file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)

    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        raise VendorChangelogError(f"{path}: entries must be an array")

    if any(str(item.get("id")) == entry["id"] for item in entries if isinstance(item, dict)):
        raise VendorChangelogError(f"entry id {entry['id']!r} already exists in {path}")

    entries.append(entry)
    payload["entries"] = _sort_entries(entries)
    payload["generated"] = date.today().isoformat()

    if dry_run:
        print(json.dumps(entry, indent=2, sort_keys=True))
        return path

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    load_vendor_changelog(path)
    return path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a vendor changelog entry safely.")
    parser.add_argument("--vendor", required=True, help="Vendor slug (e.g. cisco).")
    parser.add_argument("--dry-run", action="store_true", help="Print entry JSON without writing.")
    parser.add_argument("--product", required=True, help="Equipment model slug (e.g. asa).")
    parser.add_argument("--product-display", default="", help="Human-readable product name.")
    parser.add_argument("--release", required=True, help="Vendor release label.")
    parser.add_argument("--release-date", required=True, help="Release date YYYY-MM-DD.")
    parser.add_argument("--change-kind", required=True, dest="change_kind")
    parser.add_argument("--summary", required=True)
    parser.add_argument("--details", required=True)
    parser.add_argument("--spl-impact", required=True, dest="spl_impact")
    parser.add_argument("--source-url", required=True, dest="source_url")
    parser.add_argument(
        "--source-kind",
        default="release-notes",
        choices=[
            "release-notes",
            "security-advisory",
            "field-guide",
            "api-changelog",
            "maintainer-note",
        ],
    )
    parser.add_argument(
        "--severity",
        default="minor",
        choices=["info", "minor", "major", "critical"],
    )
    parser.add_argument("--added-by", default="maintainer")
    parser.add_argument("--categories", nargs="+", default=[], help="Affected UC categories.")
    parser.add_argument("--fields-added", nargs="*", default=[])
    parser.add_argument("--fields-removed", nargs="*", default=[])
    parser.add_argument("--fields-deprecated", nargs="*", default=[])
    parser.add_argument("--rename-from", default="")
    parser.add_argument("--rename-to", default="")
    parser.add_argument(
        "--entry-id",
        default="",
        help="Optional explicit entry id; auto-generated when omitted.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    path = _vendor_path(args.vendor)
    try:
        load_vendor_changelog(path)
    except VendorChangelogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    release_year = int(args.release_date.split("-", maxsplit=1)[0])
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    raw_entries = raw.get("entries", [])
    if not isinstance(raw_entries, list):
        print(f"ERROR: {path}: entries must be an array", file=sys.stderr)
        return 2

    entry_id = args.entry_id or _next_entry_id(args.vendor, raw_entries, release_year)

    entry = _build_entry_from_args(args, entry_id)
    try:
        written = add_entry(args.vendor, entry, dry_run=args.dry_run)
    except VendorChangelogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Dry run OK for {written}")
        return 0

    print(f"Added {entry_id} to {written.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
