#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/catalog_schema.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-catalog-schema`` dispatcher. This
shim keeps the legacy ``python3 scripts/audit_catalog_schema.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.catalog_schema import (
    CAT_META_KEY_PATTERN,
    CATALOG_PATH,
    PREREQ_UC_PATTERN,
    REPO_ROOT,
    REQUIRED_TOP_LEVEL,
    ROADMAP_WAVE_KEYS,
    UC_ID_PATTERN,
    VALID_WAVES,
    err,
    is_int,
    is_str,
    main,
)

__all__ = [
    "CATALOG_PATH",
    "CAT_META_KEY_PATTERN",
    "PREREQ_UC_PATTERN",
    "REPO_ROOT",
    "REQUIRED_TOP_LEVEL",
    "ROADMAP_WAVE_KEYS",
    "UC_ID_PATTERN",
    "VALID_WAVES",
    "err",
    "is_int",
    "is_str",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
