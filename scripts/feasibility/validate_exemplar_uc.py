#!/usr/bin/env python3
"""Phase 0.5c feasibility proof — validate the exemplar UC against the draft schema.

Run:
    .venv-feasibility/bin/python scripts/feasibility/validate_exemplar_uc.py

Exits 0 on success, 1 on any validation failure. Intentionally minimal: this is a
feasibility spike, not the production CI gate. The production gate will live in
``scripts/audit_compliance_mappings.py`` (Phase 1.5c).
"""

from __future__ import annotations

import json
import pathlib
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - run from the feasibility venv
    sys.stderr.write(
        "jsonschema not installed. Run:\n"
        "  python3 -m venv .venv-feasibility\n"
        "  .venv-feasibility/bin/python -m pip install jsonschema referencing\n"
    )
    sys.exit(2)

REPO = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO / "schemas" / "uc.schema.json"
EXEMPLAR_PATH = REPO / "use-cases" / "cat-22" / "uc-22.35.1.json"


def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    uc = load_json(EXEMPLAR_PATH)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(uc), key=lambda err: list(err.absolute_path))

    if not errors:
        print(f"PASS: {EXEMPLAR_PATH.relative_to(REPO)} conforms to {SCHEMA_PATH.relative_to(REPO)}")
        return 0

    print(
        f"FAIL: {EXEMPLAR_PATH.relative_to(REPO)} has {len(errors)} schema violation(s):\n",
        file=sys.stderr,
    )
    for err in errors:
        pointer = "/".join(str(segment) for segment in err.absolute_path) or "(root)"
        print(f"  - {pointer}: {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
