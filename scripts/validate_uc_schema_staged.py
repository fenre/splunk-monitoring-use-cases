#!/usr/bin/env python3
"""Pre-commit hook: validate staged UC sidecars against uc.schema.json.

Phase 0 hygiene helper. Called by `.pre-commit-config.yaml` with the list
of staged UC JSON files. We only validate what's about to be committed,
keeping the hook fast (<1s on a typical PR).

The full-corpus audit lives in `scripts/audit_uc_structure.py` and runs
in CI on every PR.

Exit codes:
  0  - all staged files validate
  1  - one or more files fail validation (paths printed)
  2  - schema or jsonschema unavailable (skip with a warning)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"


def main(argv: list[str]) -> int:
    if not SCHEMA_PATH.exists():
        print(
            f"warn: {SCHEMA_PATH.relative_to(REPO_ROOT)} not found; "
            "skipping pre-commit schema check.",
            file=sys.stderr,
        )
        return 0

    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        print(
            "warn: jsonschema not installed; skipping pre-commit schema check.\n"
            "      pip install jsonschema  # to enable",
            file=sys.stderr,
        )
        return 0

    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        schema = json.load(fh)

    validator = jsonschema.Draft202012Validator(schema)

    failed: list[tuple[Path, str]] = []
    for path_str in argv[1:]:
        path = Path(path_str)
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            failed.append((path, f"invalid JSON: {exc}"))
            continue

        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        for err in errors:
            location = "/".join(str(p) for p in err.absolute_path) or "<root>"
            failed.append((path, f"{location}: {err.message}"))

    if failed:
        print("UC schema validation failed:", file=sys.stderr)
        for path, msg in failed:
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            print(f"  {rel}: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
