#!/usr/bin/env python3
"""Audit Splunkbase app ID references in the use-case catalog.

Extracts every reference of the form ``splunkbase.splunk.com/app/<NUM>`` from
all markdown files under ``use-cases/`` and reports:

1. Total unique IDs and their reference counts.
2. Surrounding "context" name (best-effort preceding 80 chars) per reference.
3. IDs that appear with multiple distinct surrounding names.

It does NOT modify any files. Use the output to drive manual cleanup.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from collections import Counter, defaultdict

# parents[3] resolves: splunkbase_ids.py -> audits/ -> splunk_uc/ ->
# src/ -> repo root. The legacy two-level dirname chain is now wrong by
# three.
REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)),
        ),
    ),
)

URL_RE = re.compile(
    r"(?:\[(?P<md_name>[^\]]{1,80})\]\()?"
    r"(?:https?://)?splunkbase\.splunk\.com/app/(?P<id>\d+)"
    r"(?:/[#a-zA-Z0-9_\-/?=&]*)?"
    r"\)?"
)

SPLUNKBASE_INLINE_RE = re.compile(r"\bSplunkbase\s*#?\s*(?P<id>\d{3,5})\b", re.IGNORECASE)

NEARBY_NAME_RE = re.compile(
    r"""(?P<name>
        (?:Splunk\s+Add-[Oo]n\s+for\s+[A-Za-z0-9_\-]+(?:\s+[A-Za-z0-9_\-]+){0,5})
        | (?:[A-Z][A-Za-z0-9_\-]*\s+Add-[Oo]n(?:\s+for\s+Splunk)?)
        | (?:Splunk_TA_[a-z0-9_]+)
        | (?:TA-[a-zA-Z0-9_\-]+)
        | (?:DA-ESS-[A-Za-z0-9_]+)
        | (?:Splunk\s+App\s+for\s+[A-Za-z0-9_\-]+(?:\s+[A-Za-z0-9_\-]+){0,5})
    )""",
    re.VERBOSE,
)


def walk_files() -> list[str]:
    return sorted(glob.glob(os.path.join(REPO_ROOT, "use-cases", "cat-*.md")))


def extract_refs(path: str) -> list[tuple[str, str, str]]:
    """Return list of ``(app_id, app_name, source_file)``. ``app_name`` is best-effort."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out: list[tuple[str, str, str]] = []
    seen_spans: list[tuple[int, int]] = []
    for m in URL_RE.finditer(text):
        aid = m.group("id")
        md_name = m.group("md_name")
        name: str
        if md_name and len(md_name) < 80 and "{" not in md_name:
            name = md_name.strip()
        else:
            window = text[max(0, m.start() - 120) : m.start()]
            # Take the last name match in the lookback window (closest to
            # the URL). ``finditer`` doesn't expose ``[-1]`` directly so we
            # materialise the matches.
            nearby_matches = list(NEARBY_NAME_RE.finditer(window))
            nm = nearby_matches[-1] if nearby_matches else None
            if nm is not None:
                name = nm.group("name").strip()
            else:
                name = "<unknown>"
        name = re.sub(r"\s+", " ", name).rstrip(".,:;")
        out.append((aid, name, os.path.basename(path)))
        seen_spans.append((m.start(), m.end()))

    for m in SPLUNKBASE_INLINE_RE.finditer(text):
        span = (m.start(), m.end())
        if any(s <= span[0] <= e for s, e in seen_spans):
            continue
        aid = m.group("id")
        window = text[max(0, m.start() - 160) : m.start()]
        # Same "closest preceding TA name" semantics as above.
        nearby_matches = list(NEARBY_NAME_RE.finditer(window))
        nm = nearby_matches[-1] if nearby_matches else None
        name = nm.group("name").strip() if nm is not None else "<unknown>"
        name = re.sub(r"\s+", " ", name).rstrip(".,:;")
        out.append((aid, name, os.path.basename(path)))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Splunkbase app ID references across use-cases/cat-*.md. "
            "Informational only; does not modify files."
        )
    )
    parser.parse_args(argv)

    files = walk_files()
    refs: list[tuple[str, str, str]] = []
    for f in files:
        refs.extend(extract_refs(f))

    by_id: dict[str, Counter[str]] = defaultdict(Counter)
    for aid, name, _src in refs:
        by_id[aid][name] += 1

    print(f"Scanned {len(files)} markdown files")
    print(f"Splunkbase references: {len(refs)}")
    print(f"Unique app IDs: {len(by_id)}")
    print()

    known_unknown = sum(1 for _aid, name, _src in refs if name == "<unknown>")
    print(f"References with <unknown> context name: {known_unknown}")
    print()

    multi = {aid: counts for aid, counts in by_id.items() if len(counts) > 1}
    print(f"\nIDs with multiple observed name variants ({len(multi)}):")
    for aid in sorted(multi.keys(), key=lambda x: int(x)):
        counts = multi[aid]
        total = sum(counts.values())
        canonical, _ = counts.most_common(1)[0]
        print(f"\n  ID {aid}  (refs: {total}, canonical: {canonical!r})")
        for name, c in counts.most_common():
            print(f"      {c:3d}x  {name!r}")

    print(f"\n\nAll {len(by_id)} unique IDs, sorted by ID:")
    for aid in sorted(by_id.keys(), key=lambda x: int(x)):
        counts = by_id[aid]
        total = sum(counts.values())
        most_name, _ = counts.most_common(1)[0]
        print(f"  {aid:>6}  {total:>4}x  {most_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
