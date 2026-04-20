#!/usr/bin/env python3
"""tools.audits.schema_meta — assert every JSON Schema declares its lifecycle.

Per docs/schema-versioning.md every file under ``schemas/`` matching
``*.schema.json`` MUST declare:

* ``$schema`` (Draft 2020-12 or later)
* ``$id`` (permanent absolute URL embedding the schema major version)
* ``version`` (semver)
* ``x-stability`` (``stable``, ``preview``, or ``deprecated``)
* ``x-since`` (catalogue version where this schema first shipped)
* ``x-changelog`` (path under ``/schemas/changelogs/``)

Usage
-----
    python3 tools/audits/schema_meta.py
    python3 tools/audits/schema_meta.py --schemas schemas

Exit codes
----------
0 — every schema declares the required metadata
1 — at least one schema is missing required metadata
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("$schema", "$id", "version", "x-stability", "x-since", "x-changelog")
ALLOWED_STABILITY = {"stable", "preview", "deprecated"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="schema_meta")
    parser.add_argument("--schemas", default="schemas", help="Schemas root directory.")
    args = parser.parse_args(argv)

    root = Path(args.schemas).resolve()
    if not root.exists():
        sys.stderr.write(f"[schema_meta] missing schemas dir: {root}\n")
        return 1

    bad: list[tuple[Path, list[str]]] = []
    total = 0
    for path in sorted(root.rglob("*.schema.json")):
        total += 1
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            bad.append((path, [f"invalid JSON: {e}"]))
            continue
        problems: list[str] = []
        for key in REQUIRED:
            if key not in obj:
                problems.append(f"missing {key!r}")
        stability = obj.get("x-stability")
        if stability is not None and stability not in ALLOWED_STABILITY:
            problems.append(
                f"x-stability must be one of {sorted(ALLOWED_STABILITY)}; got {stability!r}"
            )
        if problems:
            bad.append((path, problems))

    if not bad:
        sys.stdout.write(f"[schema_meta] OK ({total} schemas)\n")
        return 0

    sys.stderr.write(
        f"[schema_meta] FAIL: {len(bad)}/{total} schema(s) missing required metadata.\n"
        f"See docs/schema-versioning.md for the contract.\n\n"
    )
    for path, problems in bad:
        sys.stderr.write(f"  {path}:\n")
        for p in problems:
            sys.stderr.write(f"    - {p}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
