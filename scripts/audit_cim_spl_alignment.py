#!/usr/bin/env python3
"""Compatibility shim - implementation in ``splunk_uc.audits.cim_spl_alignment``.

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

from splunk_uc.audits.cim_spl_alignment import (
    CANONICAL_DATAMODELS,
    RE_CIM_MODELS,
    RE_CIM_SPL_BLOCK,
    RE_DATAMODEL,
    RE_UC_HEAD,
    REPO,
    TOKEN_NORMALISATION,
    USE_CASES,
    Finding,
    _check_uc,
    _extract_datamodels_from_spl,
    _extract_declared_models,
    _iter_uc_blocks,
    audit_file,
    main,
)

__all__ = [
    "CANONICAL_DATAMODELS",
    "REPO",
    "RE_CIM_MODELS",
    "RE_CIM_SPL_BLOCK",
    "RE_DATAMODEL",
    "RE_UC_HEAD",
    "TOKEN_NORMALISATION",
    "USE_CASES",
    "Finding",
    "_check_uc",
    "_extract_datamodels_from_spl",
    "_extract_declared_models",
    "_iter_uc_blocks",
    "audit_file",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
