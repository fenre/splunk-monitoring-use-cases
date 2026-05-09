#!/usr/bin/env python3
"""tools.audits.splunkbase_coverage — track v9.0 splunkbaseApps[] migration.

Phase 4-style migration audit. Every UC is expected to either:

  (a) have a non-empty ``splunkbaseApps[]`` array with **at least one** entry
      that has been signed off (``requiresSmeReview`` is absent or false), or
  (b) be flagged as not-yet-migrated by the migration generator (every entry
      still carries ``requiresSmeReview: true``).

Until v9.0 GA the audit is **soft**: it reports coverage statistics but exits
0 on outstanding-review entries. Run with ``--strict`` to fail on any UC that
lacks ``splunkbaseApps[]`` entirely OR where every entry is still flagged.

The audit also fails in ``--strict`` mode on any structurally bad entry that
slipped past JSON-schema validation (e.g. an entry whose role is not in the
canonical enum). The schema is the first line of defence; this audit is a
belt-and-braces check focused specifically on migration progress.

Usage
-----
    python3 tools/audits/splunkbase_coverage.py
    python3 tools/audits/splunkbase_coverage.py --strict
    python3 tools/audits/splunkbase_coverage.py --json reports/coverage.json

Exit codes
----------
0 — coverage report printed; in ``--strict`` mode coverage is at 100 %.
1 — ``--strict`` mode and at least one UC fails the gate.
2 — invocation error or unreadable input file.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Dict, Iterable, List, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "content"
UC_FILE_GLOB = "cat-*/UC-*.json"

CANONICAL_ROLES = {"primary", "data-source", "premium", "optional"}


def _read_uc(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _structural_errors(entries: Iterable[Any]) -> List[str]:
    errors: List[str] = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry [{idx}] is not an object")
            continue
        missing = [k for k in ("id", "name", "role") if not entry.get(k)]
        if missing:
            errors.append(f"entry [{idx}] missing required fields {missing}")
        if entry.get("role") and entry["role"] not in CANONICAL_ROLES:
            errors.append(
                f"entry [{idx}] role={entry['role']!r} is not in {sorted(CANONICAL_ROLES)}"
            )
        url = entry.get("url")
        if url and not (
            isinstance(url, str)
            and url.startswith("https://splunkbase.splunk.com/app/")
        ):
            errors.append(f"entry [{idx}] url is not under splunkbase.splunk.com/app/")
    return errors


def _classify(uc: Dict[str, Any]) -> Tuple[str, int, int, List[str]]:
    """Return ``(state, signed_count, open_count, errors)``.

    ``state`` is one of:
      - "missing"        : no splunkbaseApps[] field, or empty array
      - "open"           : every entry has requiresSmeReview: true
      - "partial"        : some entries signed, some still flagged
      - "signed"         : every entry signed off
      - "broken"         : structural errors regardless of sign-off state
    """

    entries = uc.get("splunkbaseApps")
    if not isinstance(entries, list) or not entries:
        return ("missing", 0, 0, [])

    errors = _structural_errors(entries)
    if errors:
        return ("broken", 0, 0, errors)

    signed = sum(1 for e in entries if not e.get("requiresSmeReview"))
    open_ = len(entries) - signed
    if signed == 0:
        return ("open", 0, open_, [])
    if open_ == 0:
        return ("signed", signed, 0, [])
    return ("partial", signed, open_, [])


def _category_of(path: pathlib.Path) -> str:
    return path.parent.name


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="splunkbase_coverage")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any UC that is in 'missing' or 'open' state (post-GA mode).",
    )
    parser.add_argument(
        "--json",
        help="Optional path: write the per-category breakdown as JSON.",
    )
    args = parser.parse_args(argv)

    if not CONTENT_DIR.is_dir():
        print(f"[splunkbase_coverage] missing content dir: {CONTENT_DIR}", file=sys.stderr)
        return 2

    counts: Dict[str, int] = {
        "total": 0,
        "missing": 0,
        "open": 0,
        "partial": 0,
        "signed": 0,
        "broken": 0,
    }
    by_category: Dict[str, Dict[str, int]] = {}
    broken_examples: List[Tuple[str, List[str]]] = []
    failing_ucs: List[str] = []

    for path in sorted(CONTENT_DIR.glob(UC_FILE_GLOB)):
        try:
            uc = _read_uc(path)
        except (OSError, json.JSONDecodeError) as err:
            print(f"[splunkbase_coverage] {path}: {err}", file=sys.stderr)
            return 2
        state, signed, open_, errors = _classify(uc)
        counts["total"] += 1
        counts[state] += 1
        cat = _category_of(path)
        bucket = by_category.setdefault(
            cat,
            {"total": 0, "missing": 0, "open": 0, "partial": 0, "signed": 0, "broken": 0},
        )
        bucket["total"] += 1
        bucket[state] += 1
        if state == "broken":
            broken_examples.append((str(path.relative_to(REPO_ROOT)), errors))
        if args.strict and state in ("missing", "open", "broken"):
            failing_ucs.append(str(path.relative_to(REPO_ROOT)))

    pct_signed = (
        (counts["signed"] + counts["partial"]) / counts["total"] * 100
        if counts["total"]
        else 0.0
    )

    print(
        f"[splunkbase_coverage] total={counts['total']} "
        f"signed={counts['signed']} partial={counts['partial']} "
        f"open={counts['open']} missing={counts['missing']} "
        f"broken={counts['broken']} coverage={pct_signed:.1f}%"
    )

    if args.json:
        out = {
            "summary": {**counts, "coveragePct": round(pct_signed, 2)},
            "byCategory": {
                cat: {
                    **vals,
                    "coveragePct": round(
                        ((vals["signed"] + vals["partial"]) / vals["total"]) * 100, 2
                    )
                    if vals["total"]
                    else 0.0,
                }
                for cat, vals in sorted(by_category.items())
            },
        }
        out_path = pathlib.Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    for path, errs in broken_examples[:5]:
        print(f"[splunkbase_coverage] BROKEN {path}", file=sys.stderr)
        for err in errs:
            print(f"  - {err}", file=sys.stderr)
    if len(broken_examples) > 5:
        print(
            f"[splunkbase_coverage] ... and {len(broken_examples) - 5} more broken UCs",
            file=sys.stderr,
        )

    if args.strict and failing_ucs:
        print(
            f"[splunkbase_coverage] STRICT FAIL: {len(failing_ucs)} UCs lack signed off "
            "Splunkbase mappings (or have structural errors).",
            file=sys.stderr,
        )
        for path in failing_ucs[:10]:
            print(f"  - {path}", file=sys.stderr)
        if len(failing_ucs) > 10:
            print(f"  ... and {len(failing_ucs) - 10} more", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
