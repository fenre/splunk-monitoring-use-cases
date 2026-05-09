#!/usr/bin/env python3
"""Compatibility shim — implementation moved to ``splunk_uc.audits.nis2_no_gap``.

This file is kept so legacy invocations of ``python3
scripts/audit_nis2_no_gap.py`` and any in-tree imports of
``scripts.audit_nis2_no_gap`` continue to work during the P6 migration
soak window. It is a thin re-export of the public surface of the
canonical implementation under ``src/splunk_uc/audits/``.

New callers should use either:

* the dispatcher: ``python -m splunk_uc audit-nis2-no-gap``
* the make target: ``make audit-nis2-no-gap``

The shim will be deleted at the end of the P6 Tier 3 soak period
(see docs/scripts-taxonomy.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.nis2_no_gap import (
    CONTENT_ROOT,
    MATRIX_PATH,
    REPO_ROOT,
    REQUIRED_ROW_FIELDS,
    SOURCE_MAP_PATH,
    VALID_ASSURANCE,
    VALID_CONFIDENCE,
    VALID_COVERAGE,
    VALID_UC_PLAN,
    _is_non_empty,
    _iter_nis2_compliance_entries,
    _load_json,
    _validate_matrix,
    _validate_uc_traceability,
    main,
)

__all__ = [
    "CONTENT_ROOT",
    "MATRIX_PATH",
    "REPO_ROOT",
    "REQUIRED_ROW_FIELDS",
    "SOURCE_MAP_PATH",
    "VALID_ASSURANCE",
    "VALID_CONFIDENCE",
    "VALID_COVERAGE",
    "VALID_UC_PLAN",
    "_is_non_empty",
    "_iter_nis2_compliance_entries",
    "_load_json",
    "_validate_matrix",
    "_validate_uc_traceability",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
