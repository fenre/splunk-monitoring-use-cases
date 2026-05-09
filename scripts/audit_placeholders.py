#!/usr/bin/env python3
"""Compatibility shim - implementation in ``splunk_uc.audits.placeholders``.

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

from splunk_uc.audits.placeholders import (
    RE_EDITORIAL_HEADER,
    RE_FIELD,
    RE_KNOWN_FP,
    RE_SECTION_HEAD,
    RE_SPL_FENCE,
    RE_UC_HEAD,
    REPO_ROOT,
    USE_CASES,
    Finding,
    _check_editorial_headers,
    _check_known_fp_blank,
    _check_markers,
    _iter_uc_blocks,
    audit_file,
    main,
)

__all__ = [
    "REPO_ROOT",
    "RE_EDITORIAL_HEADER",
    "RE_FIELD",
    "RE_KNOWN_FP",
    "RE_SECTION_HEAD",
    "RE_SPL_FENCE",
    "RE_UC_HEAD",
    "USE_CASES",
    "Finding",
    "_check_editorial_headers",
    "_check_known_fp_blank",
    "_check_markers",
    "_iter_uc_blocks",
    "audit_file",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
