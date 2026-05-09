#!/usr/bin/env python3
"""Compatibility shim - implementation in ``splunk_uc.audits.legal_review_signoffs``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.
See ``docs/scripts-taxonomy.md`` for the migration recipe.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.legal_review_signoffs import (
    DATA_PATH,
    REPO,
    SCHEMA_PATH,
    USE_CASES,
    _collect_uc_legal_caveats,
    _load_json,
    _print_summary,
    _uc_sidecar_path,
    _validate_schema,
    _validate_semantics,
    main,
)

__all__ = [
    "DATA_PATH",
    "REPO",
    "SCHEMA_PATH",
    "USE_CASES",
    "_collect_uc_legal_caveats",
    "_load_json",
    "_print_summary",
    "_uc_sidecar_path",
    "_validate_schema",
    "_validate_semantics",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
