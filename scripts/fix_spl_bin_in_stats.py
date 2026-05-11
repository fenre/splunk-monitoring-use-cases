#!/usr/bin/env python3
"""Fix UCs where `bin(_time, Xh)` is used as a stats/eventstats `by`
clause field. `bin()` is NOT an eval/stats function — it's a standalone
command. The correct form is to insert `| bin _time span=Xh` before the
stats command and use `_time` in the by-clause.

Example transformation:

    | stats count by function_name, bin(_time, 1h)
                                                    ↓
    | bin _time span=1h
    | stats count by function_name, _time

Pass --write to apply.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

# Match the inline bin() call inside a by-clause (or anywhere stats-ish)
BIN_INLINE_RE = re.compile(
    r"\bbin\(\s*(?P<field>[A-Za-z_][A-Za-z0-9_.]*)\s*,\s*(?P<span>[0-9]+[smhdw])\s*\)",
    re.IGNORECASE,
)


def fix_spl(spl: str) -> tuple[str, list[str]]:
    """Return (new_spl, change_list)."""
    changes: list[str] = []
    matches = list(BIN_INLINE_RE.finditer(spl))
    if not matches:
        return spl, changes

    # Collect (field, span) pairs we need to bin before stats; deduplicate
    bins_to_add: list[tuple[str, str]] = []
    seen = set()
    for m in matches:
        key = (m.group("field"), m.group("span"))
        if key not in seen:
            seen.add(key)
            bins_to_add.append(key)
    # Replace bin(field, span) -> field
    new_spl = BIN_INLINE_RE.sub(lambda m: m.group("field"), spl)
    changes.append(
        f"replaced inline bin() calls with bare field refs ({len(matches)} occurrences)"
    )
    # Prepend the bin commands BEFORE the first stats/timechart/eventstats
    # to preserve order and avoid duplicate bin headers.
    first_stats = re.search(
        r"\|\s*(?:stats|timechart|eventstats|streamstats|chart)\b",
        new_spl,
    )
    if first_stats:
        head = new_spl[: first_stats.start()].rstrip()
        tail = new_spl[first_stats.start():]
        bin_lines = " ".join(
            f"| bin {f} span={s}" for f, s in bins_to_add
        )
        new_spl = f"{head}\n{bin_lines}\n{tail}"
        changes.append(
            f"prepended `{bin_lines.strip()}` before stats family command"
        )
    return new_spl, changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    fixed_files = 0
    total_changes = 0
    samples: list[tuple[str, list[str]]] = []
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        spl = d.get("spl")
        if not isinstance(spl, str):
            continue
        # only operate on UCs where bin() is inside a stats-family by-clause
        m = re.search(
            r"\b(?:stats|eventstats|streamstats|chart|timechart)\b[^|]*\bby\s+[^|]*bin\(",
            spl,
        )
        if not m:
            continue
        new_spl, changes = fix_spl(spl)
        if changes:
            d["spl"] = new_spl
            if args.write:
                p.write_text(
                    json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            fixed_files += 1
            total_changes += len(changes)
            if len(samples) < 5:
                samples.append((p.name, changes))

    print(f"Files fixed: {fixed_files}")
    print(f"Total transformations: {total_changes}")
    for name, ch in samples:
        print(f"  [{name}]: {'; '.join(ch)}")
    if not args.write:
        print("\nDRY RUN — pass --write to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
