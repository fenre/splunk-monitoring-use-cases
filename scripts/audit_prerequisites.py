#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.prerequisites``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_prerequisites.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-prerequisites``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.prerequisites import (
    CATALOG_PATH,
    PREREQ_UC_PATTERN,
    REPO_ROOT,
    REPORT_PATH,
    UC_ID_PATTERN,
    VALID_WAVES,
    WAVE_RANK,
    main,
)

__all__ = [
    "CATALOG_PATH",
    "PREREQ_UC_PATTERN",
    "REPORT_PATH",
    "REPO_ROOT",
    "UC_ID_PATTERN",
    "VALID_WAVES",
    "WAVE_RANK",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
