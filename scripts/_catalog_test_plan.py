"""Build a catalog-wide test plan: every UC whose SPL targets a sourcetype
that has live data on this Splunk lab.

Reads /tmp/all-st-counts.json (mapping sourcetype -> 90d count). Selects
every UC whose primary leading-search sourcetype is present with > 0 events.
Writes /tmp/catalog-test-plan.jsonl with one row per UC.

Usage:
    python3 scripts/_catalog_test_plan.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
ST_COUNTS = Path("/tmp/all-st-counts.json")

ST_RE = re.compile(r'sourcetype\s*=\s*"?([\w:.\-]+)"?', re.I)


def primary_sourcetype(spl: str) -> str:
    """Return the sourcetype mentioned BEFORE the first `|` (leading search)."""
    s = spl.lstrip()
    if s.startswith("|"):
        # Generating command - look at the first segment.
        first = s.split("|", 2)[1] if "|" in s[1:] else s
    else:
        first = s.split("|", 1)[0]
    m = ST_RE.search(first)
    return m.group(1).lower() if m else ""


def all_sourcetypes(spl: str) -> list[str]:
    return sorted({m.group(1).lower() for m in ST_RE.finditer(spl)})


def main() -> int:
    if not ST_COUNTS.exists():
        print(f"Run the data-presence probe first to create {ST_COUNTS}",
              file=sys.stderr)
        return 2

    counts = json.load(open(ST_COUNTS))
    rows = []
    for path in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(open(path))
        except Exception:
            continue
        spl = d.get("spl") or ""
        if not spl:
            continue
        primary = primary_sourcetype(spl)
        if not primary:
            continue
        primary_count = counts.get(primary, 0)
        if primary_count <= 0:
            continue  # Untestable here
        rows.append({
            "uc_id": d.get("id", ""),
            "title": d.get("title", ""),
            "path": str(path.relative_to(ROOT)),
            "spl": spl,
            "primary": primary,
            "primary_count": primary_count,
            "sourcetypes": all_sourcetypes(spl),
        })

    rows.sort(key=lambda r: (r["primary"], r["uc_id"]))
    for r in rows:
        print(json.dumps(r))

    # Brief summary on stderr.
    print(f"\nWrote {len(rows)} UCs to test plan", file=sys.stderr)
    from collections import Counter
    by_st = Counter(r["primary"] for r in rows)
    for st, n in by_st.most_common(30):
        print(f"  {n:>4d} UCs on {st} (live count: {counts.get(st, 0):,d})",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
