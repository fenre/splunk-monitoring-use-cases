#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.sandbox_validation``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_sandbox_validation.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-sandbox-validation``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.sandbox_validation import (
    FIXTURE_SHAPE_LEGACY,
    HARD_FAIL_STATUSES,
    REPO,
    REPORT_PATH,
    SAMPLE_DATA,
    STATUS_BAD_JSON,
    STATUS_EMPTY,
    STATUS_HALF_EMPTY,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_POPULATED,
    USE_CASES,
    main,
)

__all__ = [
    "FIXTURE_SHAPE_LEGACY",
    "HARD_FAIL_STATUSES",
    "REPO",
    "REPORT_PATH",
    "SAMPLE_DATA",
    "STATUS_BAD_JSON",
    "STATUS_EMPTY",
    "STATUS_HALF_EMPTY",
    "STATUS_MALFORMED",
    "STATUS_MISSING",
    "STATUS_POPULATED",
    "USE_CASES",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
