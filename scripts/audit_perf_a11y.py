#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.perf_a11y``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_perf_a11y.py`` invocation alive while the
new dispatcher (``python -m splunk_uc audit-perf-a11y``) becomes the
primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.perf_a11y import (
    REPO,
    REPORT_PATH,
    RUN_AXE_SCRIPT,
    PerfBudget,
    main,
)

__all__ = [
    "REPO",
    "REPORT_PATH",
    "RUN_AXE_SCRIPT",
    "PerfBudget",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
