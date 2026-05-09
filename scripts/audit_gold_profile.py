#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.gold_profile``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_gold_profile.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-gold-profile``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.gold_profile import (
    BRONZE_MIN_LENGTHS,
    BRONZE_REQUIRED,
    CONTENT_DIR,
    GENERIC_BOILERPLATE_PHRASES,
    GOLD_MIN_LENGTHS,
    GOLD_REQUIRED,
    PRODUCT_SPECIFIC_INDICATORS,
    REPO_ROOT,
    REPORT_DIR,
    SECTION_PATTERNS,
    SILVER_MIN_LENGTHS,
    SILVER_REQUIRED,
    audit_uc,
    find_consolidation_candidates,
    find_uc_files,
    main,
    print_summary,
    write_report,
)

__all__ = [
    "BRONZE_MIN_LENGTHS",
    "BRONZE_REQUIRED",
    "CONTENT_DIR",
    "GENERIC_BOILERPLATE_PHRASES",
    "GOLD_MIN_LENGTHS",
    "GOLD_REQUIRED",
    "PRODUCT_SPECIFIC_INDICATORS",
    "REPORT_DIR",
    "REPO_ROOT",
    "SECTION_PATTERNS",
    "SILVER_MIN_LENGTHS",
    "SILVER_REQUIRED",
    "audit_uc",
    "find_consolidation_candidates",
    "find_uc_files",
    "main",
    "print_summary",
    "write_report",
]


if __name__ == "__main__":
    sys.exit(main())
