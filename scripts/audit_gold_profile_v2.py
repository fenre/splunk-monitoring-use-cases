#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.gold_profile_v2``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_gold_profile_v2.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-gold-profile-v2``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.gold_profile_v2 import (
    CONTENT_DIR,
    REPO_ROOT,
    V2_THRESHOLDS,
    audit_uc_v2,
    check_pack_drift,
    find_uc_files,
    main,
    print_report,
)

__all__ = [
    "CONTENT_DIR",
    "REPO_ROOT",
    "V2_THRESHOLDS",
    "audit_uc_v2",
    "check_pack_drift",
    "find_uc_files",
    "main",
    "print_report",
]


if __name__ == "__main__":
    sys.exit(main())
