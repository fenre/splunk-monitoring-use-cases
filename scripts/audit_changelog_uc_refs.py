#!/usr/bin/env python3
"""
Repository quality checks:
1) CHANGELOG.md version headers, duplicates, dates, ordering
2) UC cross-references in use-cases/cat-*.md vs ### UC-X.Y.Z definitions
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
USE_CASES = REPO / "use-cases"

HEADER_RE = re.compile(r"^## \[(?P<ver>[^\]]+)\]\s*-\s*(?P<rest>.+?)\s*$")
UC_HEADER_RE = re.compile(r"^###\s+(UC-\d+\.\d+\.\d+)\b")
UC_REF_RE = re.compile(r"\b(UC-\d+\.\d+\.\d+)\b")


@dataclass
class ChangelogEntry:
    line: int
    version: str
    date_raw: str
    date_parsed: object | None
    line_text: str


def parse_changelog():
    issues = []
    entries = []

    if not CHANGELOG.is_file():
        issues.append(f"CHANGELOG.md not found at {CHANGELOG}")
        return entries, issues

    text = CHANGELOG.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), start=1):
        m = HEADER_RE.match(line)
        if not m:
            continue
        ver = m.group("ver").strip()
        rest = m.group("rest").strip()

        date_parsed = None
        date_raw = rest
        iso_m = re.match(
            r"^(\d{4}-\d{2}-\d{2})(?:\s*[–-]\s*\d{4}-\d{2}-\d{2})?$",
            rest,
        )
        if iso_m:
            try:
                date_parsed = datetime.strptime(iso_m.group(1), "%Y-%m-%d").date()
            except ValueError:
                issues.append(
                    f"CHANGELOG.md:{i}: Invalid calendar date in header: {line!r}"
                )
        else:
            fallback = re.search(r"(\d{4}-\d{2}-\d{2})", rest)
            if fallback:
                try:
                    date_parsed = datetime.strptime(
                        fallback.group(1), "%Y-%m-%d"
                    ).date()
                except ValueError:
                    issues.append(
                        f"CHANGELOG.md:{i}: Could not parse date from: {line!r}"
                    )
            else:
                issues.append(
                    f"CHANGELOG.md:{i}: No YYYY-MM-DD date found in header: {line!r}"
                )

        if not re.match(r"^## \[[^\]]+\] - .+", line):
            issues.append(
                f"CHANGELOG.md:{i}: Unexpected header shape (expected '## [ver] - date'): {line!r}"
            )

        entries.append(
            ChangelogEntry(
                line=i,
                version=ver,
                date_raw=date_raw,
                date_parsed=date_parsed,
                line_text=line,
            )
        )

    return entries, issues


def validate_changelog(entries):
    issues = []

    seen = {}
    for e in entries:
        seen.setdefault(e.version, []).append(e.line)
    for ver, lines in sorted(seen.items(), key=lambda x: x[0]):
        if len(lines) > 1:
            issues.append(
                f"Duplicate version heading [{ver}] at lines: {', '.join(map(str, lines))}"
            )

    parsed = [(e, e.date_parsed) for e in entries]
    for j in range(len(parsed) - 1):
        a, da = parsed[j]
        b, db = parsed[j + 1]
        if da is not None and db is not None and db > da:
            issues.append(
                f"CHANGELOG ordering: line {b.line} date {db} is newer than line {a.line} date {da} "
                f"(expected monotonically non-increasing dates top to bottom)"
            )

    return issues


def collect_uc_definitions():
    valid = set()
    issues = []
    paths = sorted(USE_CASES.glob("cat-*.md"))
    for p in paths:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            m = UC_HEADER_RE.match(line.strip())
            if m:
                uc_id = m.group(1)
                if uc_id in valid:
                    issues.append(
                        f"Duplicate UC definition {uc_id}: {p.name}:{i} (also defined earlier)"
                    )
                valid.add(uc_id)
    return valid, issues


def validate_uc_refs(valid):
    issues = []
    paths = sorted(USE_CASES.glob("cat-*.md"))
    for p in paths:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
            for m in UC_REF_RE.finditer(line):
                uc_id = m.group(1)
                if uc_id not in valid:
                    issues.append(
                        f"Broken UC cross-reference {uc_id}: {p.name}:{i}: {line.strip()[:240]}"
                    )
    return issues


def main():
    all_issues = []

    entries, cl_issues = parse_changelog()
    all_issues.extend(cl_issues)
    all_issues.extend(validate_changelog(entries))

    valid_ucs, dup_uc_issues = collect_uc_definitions()
    all_issues.extend(dup_uc_issues)
    all_issues.extend(validate_uc_refs(valid_ucs))

    print("=== CHANGELOG summary ===")
    print(f"Parsed {len(entries)} version headers from CHANGELOG.md")
    for e in entries[:5]:
        print(f"  [{e.version}] @ L{e.line} date={e.date_parsed}")
    if len(entries) > 5:
        print(f"  ... ({len(entries) - 5} more)")
    print()

    print("=== UC catalog summary ===")
    print(f"Unique UC IDs from ### headers: {len(valid_ucs)}")
    print()

    print(f"=== ALL ISSUES ({len(all_issues)}) ===")
    if not all_issues:
        print("None.")
        return 0
    for msg in all_issues:
        print(msg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
