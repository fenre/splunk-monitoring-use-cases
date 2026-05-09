#!/usr/bin/env python3
"""Compatibility shim - implementation in ``splunk_uc.audits.regulatory_primer``.

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

from splunk_uc.audits.regulatory_primer import (
    CATEGORY_JSON,
    PRIMER,
    REGULATIONS_JSON,
    REPO_ROOT,
    Finding,
    _find_line,
    _load_framework_tiers,
    _load_uc_counts,
    audit,
    main,
)

__all__ = [
    "CATEGORY_JSON",
    "PRIMER",
    "REGULATIONS_JSON",
    "REPO_ROOT",
    "Finding",
    "_find_line",
    "_load_framework_tiers",
    "_load_uc_counts",
    "audit",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
