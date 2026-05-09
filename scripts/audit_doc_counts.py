#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.doc_counts``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_doc_counts.py`` invocation alive while the
new dispatcher (``python -m splunk_uc audit-doc-counts``) becomes the
primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.doc_counts import (
    CHECKS,
    PROJECT_ROOT,
    get_actual_category_count,
    get_actual_uc_count,
    main,
)

__all__ = [
    "CHECKS",
    "PROJECT_ROOT",
    "get_actual_category_count",
    "get_actual_uc_count",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
