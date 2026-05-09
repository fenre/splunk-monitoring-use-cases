#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/known_fp.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-known-fp`` dispatcher. This shim
keeps the legacy ``python3 scripts/audit_known_fp.py`` invocation
working unchanged for Makefile/CI/docs callers during the soak
period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.known_fp import (
    PLACEHOLDER_VALUES,
    RE_FP_LINE,
    RE_UC_HEAD,
    REPO,
    USE_CASES,
    Finding,
    _classify,
    _iter_uc_blocks,
    audit_file,
    main,
)

__all__ = [
    "PLACEHOLDER_VALUES",
    "REPO",
    "RE_FP_LINE",
    "RE_UC_HEAD",
    "USE_CASES",
    "Finding",
    "_classify",
    "_iter_uc_blocks",
    "audit_file",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
