"""Phase 0.5c feasibility proof — validate the exemplar UC against the draft schema.

P6 (scripts taxonomy, 2026-05-10) relocated this feasibility spike from
scripts/feasibility/validate_exemplar_uc.py to
src/splunk_uc/feasibility/validate_exemplar_uc.py. parents[3] resolves:
validate_exemplar_uc.py -> feasibility/ -> splunk_uc/ -> src/ -> repo
root. The legacy ``parents[2]`` chain assumed depth two and is now
wrong by one level. The legacy shim re-exports ``main`` so any direct
CLI invocation still works during the soak period.

Run:
    python -m splunk_uc feasibility-validate-exemplar

Exits 0 on success, 1 on any validation failure. Intentionally minimal: this is a
feasibility spike, not the production CI gate. The production gate lives in
``audit_compliance_mappings`` (Phase 1.5c).

NOTE: ``EXEMPLAR_PATH`` still points at the legacy ``use-cases/cat-22/``
location to preserve byte-for-byte behaviour with the original spike.
The catalogue's source-of-truth has since moved to
``content/cat-22-regulatory-compliance/UC-22.35.1.json``; updating this
spike to the JSON SSOT layout is a soak-end clean-up, not part of the
P6 migration.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - run from the feasibility venv
    sys.stderr.write(
        "jsonschema not installed. Run:\n"
        "  python3 -m venv .venv-feasibility\n"
        "  .venv-feasibility/bin/python -m pip install jsonschema referencing\n"
    )
    sys.exit(2)

REPO = pathlib.Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO / "schemas" / "uc.schema.json"
EXEMPLAR_PATH = REPO / "use-cases" / "cat-22" / "uc-22.35.1.json"


def load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload: dict[str, Any] = json.load(handle)
        return payload


def main(argv: list[str] | None = None) -> int:
    """Dispatcher entry-point. ``argv`` accepted for the registry contract; this spike takes no flags."""
    del argv
    schema = load_json(SCHEMA_PATH)
    uc = load_json(EXEMPLAR_PATH)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(uc), key=lambda err: list(err.absolute_path))

    if not errors:
        print(
            f"PASS: {EXEMPLAR_PATH.relative_to(REPO)} conforms to {SCHEMA_PATH.relative_to(REPO)}"
        )
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
