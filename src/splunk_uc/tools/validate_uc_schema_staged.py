"""Pre-commit hook: validate staged UC sidecars against uc.schema.json.

P6 (scripts taxonomy, 2026-05-10) relocated this driver from
scripts/validate_uc_schema_staged.py to
src/splunk_uc/tools/validate_uc_schema_staged.py. parents[3]
resolves: validate_uc_schema_staged.py -> tools/ -> splunk_uc/ ->
src/ -> repo root. The legacy ``parent.parent`` chain assumed
depth one and is now wrong by two levels. The dispatcher contract
(``main(argv: list[str] | None) -> int``) drops the legacy
``argv[0]`` program-name slot; the legacy shim re-injects it so
``.pre-commit-config.yaml`` invocations still work without a hook
config update.

Phase 0 hygiene helper. Called by ``.pre-commit-config.yaml`` with the list
of staged UC JSON files. We only validate what's about to be committed,
keeping the hook fast (<1s on a typical PR).

The full-corpus audit lives in
``python -m splunk_uc audit-uc-structure`` and runs in CI on every PR.

Exit codes:
  0  - all staged files validate
  1  - one or more files fail validation (paths printed)
  2  - schema or jsonschema unavailable (skip with a warning)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"


def main(argv: list[str] | None = None) -> int:
    """Validate the supplied UC sidecar paths against ``schemas/uc.schema.json``.

    ``argv`` is the list of file paths to check (no program-name prefix).
    """
    paths = list(sys.argv[1:] if argv is None else argv)

    if not SCHEMA_PATH.exists():
        print(
            f"warn: {SCHEMA_PATH.relative_to(REPO_ROOT)} not found; "
            "skipping pre-commit schema check.",
            file=sys.stderr,
        )
        return 0

    try:
        import jsonschema
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
    for path_str in paths:
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
                rel: Path = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            print(f"  {rel}: {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
