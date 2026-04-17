#!/usr/bin/env python3
"""Audit Splunkbase app ID references in the use-case catalog.

Extracts every reference of the form `splunkbase.splunk.com/app/<NUM>` from
all markdown files under `use-cases/` and reports:

1. Total unique IDs and their reference counts.
2. Surrounding "context" name (best-effort preceding 80 chars) per reference.
3. IDs that appear with multiple distinct surrounding names.

It does NOT modify any files.  Use the output to drive manual cleanup.
"""

import glob
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Capture every splunkbase app URL, with optional preceding `[NAME](` pattern.
# Also captures bare URLs.  The NAME is inside markdown link brackets when
# present; otherwise we fall back to pulling a nearby TA name from context.
URL_RE = re.compile(
    r"(?:\[(?P<md_name>[^\]]{1,80})\]\()?"
    r"(?:https?://)?splunkbase\.splunk\.com/app/(?P<id>\d+)"
    r"(?:/[#a-zA-Z0-9_\-/?=&]*)?"
    r"\)?"
)

# Secondary pattern: `Splunkbase 2757` or `Splunkbase #2757` or `(Splunkbase 2757)`
SPLUNKBASE_INLINE_RE = re.compile(
    r"\bSplunkbase\s*#?\s*(?P<id>\d{3,5})\b", re.IGNORECASE
)

# Look for a TA/app reference near the URL (within 100 chars).
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


def walk_files() -> List[str]:
    return sorted(glob.glob(os.path.join(REPO_ROOT, "use-cases", "cat-*.md")))


def extract_refs(path: str) -> List[Tuple[str, str, str]]:
    """Return list of (app_id, app_name, source_file). app_name is best-effort."""
    text = open(path, encoding="utf-8").read()
    out: List[Tuple[str, str, str]] = []
    seen_spans: List[Tuple[int, int]] = []
    for m in URL_RE.finditer(text):
        aid = m.group("id")
        md_name = m.group("md_name")
        name: str
        if md_name and len(md_name) < 80 and "{" not in md_name:
            name = md_name.strip()
        else:
            window = text[max(0, m.start() - 120):m.start()]
            nm = None
            for nm in NEARBY_NAME_RE.finditer(window):
                pass
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
        window = text[max(0, m.start() - 160):m.start()]
        nm = None
        for nm in NEARBY_NAME_RE.finditer(window):
            pass
        name = (nm.group("name").strip() if nm is not None else "<unknown>")
        name = re.sub(r"\s+", " ", name).rstrip(".,:;")
        out.append((aid, name, os.path.basename(path)))
    return out


def main() -> int:
    files = walk_files()
    refs: List[Tuple[str, str, str]] = []
    for f in files:
        refs.extend(extract_refs(f))

    by_id: Dict[str, Counter] = defaultdict(Counter)
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
        print(f"\n  ID {aid}  (refs: {total})")
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
