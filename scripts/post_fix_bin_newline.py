#!/usr/bin/env python3
"""Repair the ``_time| <next-pipe>`` pattern introduced by a previous run of
``fix_spl_hallucinations.py`` when ``fix_bin_in_stats_by`` consumed the
trailing newline that separated the rewritten ``stats … by _time`` line
from the next pipe segment.

The broken pattern looks like::

    | bin _time span=1h
    | stats count … by function_name, _time| eval cold_start_pct=…

We restore the newline so each pipe segment lives on its own line.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"

# Match ``, _time|`` immediately followed by an alphabetic character — meaning
# the pipe was glued directly to the next command without separating space.
PAT = re.compile(r"(,\s*_time)\|\s*([a-z])")


def main() -> int:
    n_files = 0
    n_changed = 0
    for sidecar in sorted(CONTENT_DIR.rglob("UC-*.json")):
        try:
            text = sidecar.read_text(encoding="utf-8")
            uc = json.loads(text)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR parsing {sidecar}: {exc}", file=sys.stderr)
            continue
        n_files += 1
        before = json.dumps(uc, indent=2, ensure_ascii=False)
        for fld in ("spl", "cimSpl"):
            spl = uc.get(fld, "") or ""
            if "_time|" not in spl:
                continue
            new_spl = PAT.sub(r"\1\n| \2", spl)
            if new_spl != spl:
                uc[fld] = new_spl
        after = json.dumps(uc, indent=2, ensure_ascii=False)
        if before != after:
            n_changed += 1
            sidecar.write_text(after + "\n", encoding="utf-8")
    print(f"Scanned {n_files}, repaired {n_changed} sidecars.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
