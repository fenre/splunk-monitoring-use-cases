#!/usr/bin/env python3
"""Compatibility shim - implementation in ``splunk_uc.audits.mitre_taxonomy``.

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

from splunk_uc.audits.mitre_taxonomy import (
    CONTENT_DIR,
    RE_VALID_TOKEN,
    REPO_ROOT,
    Finding,
    _check_mitre_line,
    _tokenize_mitre_body,
    audit_uc_json,
    main,
)

__all__ = [
    "CONTENT_DIR",
    "REPO_ROOT",
    "RE_VALID_TOKEN",
    "Finding",
    "_check_mitre_line",
    "_tokenize_mitre_body",
    "audit_uc_json",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
