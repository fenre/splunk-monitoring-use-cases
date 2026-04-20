#!/usr/bin/env python3
"""tools.audits.budgets — enforce per-asset-class size budgets.

Reads ``tools/build/budgets.json`` and walks ``dist/`` matching the
documented globs against each budget. A budget with ``fail_on_exceed:
true`` blocks merge to main.

Usage
-----
    python3 tools/audits/budgets.py --dist dist
    python3 tools/audits/budgets.py --dist dist --json   # CI-friendly output

Exit codes
----------
0 — all hard budgets met
1 — at least one ``fail_on_exceed: true`` budget exceeded
2 — invocation error
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_BUDGETS = PROJECT_ROOT / "tools" / "build" / "budgets.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="budgets")
    parser.add_argument("--dist", default="dist", help="Built site directory.")
    parser.add_argument(
        "--budgets",
        default=str(DEFAULT_BUDGETS),
        help="Path to budgets.json (default: tools/build/budgets.json).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report on stdout instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    dist = Path(args.dist).resolve()
    if not dist.exists():
        sys.stderr.write(f"[budgets] missing dist dir: {dist}\n")
        return 2

    spec = json.loads(Path(args.budgets).read_text(encoding="utf-8"))
    fail = False
    report = []

    for budget in spec.get("budgets", []):
        glob = budget["glob"]
        max_bytes = budget.get("max_bytes")
        max_bytes_gz = budget.get("max_bytes_gz")
        hard = bool(budget.get("fail_on_exceed", True))

        # Globs in budgets.json are anchored to ``dist/`` and use shell-style
        # wildcards. We use plain ``glob`` so a pattern like ``index.html``
        # matches only the root landing page; patterns that need to recurse
        # opt in explicitly with ``**`` (e.g. ``uc/**/index.html``).
        matches = sorted(p for p in dist.glob(glob) if p.is_file())
        violations = []
        for m in matches:
            raw = m.stat().st_size
            gz = _gzip_len(m) if max_bytes_gz else 0
            if max_bytes and raw > max_bytes:
                violations.append({"file": str(m.relative_to(dist)), "kind": "raw", "actual": raw, "max": max_bytes})
            if max_bytes_gz and gz > max_bytes_gz:
                violations.append({"file": str(m.relative_to(dist)), "kind": "gz", "actual": gz, "max": max_bytes_gz})

        report.append({
            "budget": budget["id"],
            "glob": glob,
            "matches": len(matches),
            "violations": violations,
            "hard": hard,
        })
        if hard and violations:
            fail = True

    if args.json:
        sys.stdout.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    else:
        for entry in report:
            tag = "FAIL" if entry["hard"] and entry["violations"] else (
                "WARN" if entry["violations"] else "OK"
            )
            sys.stdout.write(
                f"[budgets] {tag:4s} {entry['budget']:24s} "
                f"({entry['matches']} match, "
                f"{len(entry['violations'])} violations)\n"
            )
            for v in entry["violations"][:3]:
                sys.stdout.write(
                    f"           {v['file']}: {v['actual']:,} > {v['max']:,} bytes ({v['kind']})\n"
                )

    return 1 if fail else 0


def _gzip_len(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))


if __name__ == "__main__":
    sys.exit(main())
