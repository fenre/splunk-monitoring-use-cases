#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/spl_duplicates.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-spl-duplicates`` dispatcher. This
shim keeps the legacy ``python3 scripts/audit_spl_duplicates.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.spl_duplicates import (
    RE_MACRO_ARGS,
    RE_SPL_BLOCK,
    RE_UC_HEAD,
    RE_WS,
    REPO,
    USE_CASES,
    _canonical_spl,
    _collect,
    main,
)

__all__ = [
    "REPO",
    "RE_MACRO_ARGS",
    "RE_SPL_BLOCK",
    "RE_UC_HEAD",
    "RE_WS",
    "USE_CASES",
    "_canonical_spl",
    "_collect",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
