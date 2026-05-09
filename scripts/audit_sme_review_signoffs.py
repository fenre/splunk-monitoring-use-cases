#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.sme_review_signoffs``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_sme_review_signoffs.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-sme-review-signoffs``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.sme_review_signoffs import (
    DATA_PATH,
    EVIDENCE_PACKS,
    REPO,
    SAMPLE_DATA,
    SCHEMA_PATH,
    USE_CASES,
    main,
)

__all__ = [
    "DATA_PATH",
    "EVIDENCE_PACKS",
    "REPO",
    "SAMPLE_DATA",
    "SCHEMA_PATH",
    "USE_CASES",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
