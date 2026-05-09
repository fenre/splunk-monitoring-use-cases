#!/usr/bin/env python3
"""Per-regulation clause-level gap analysis (legacy shim).

Phase 6 of the repo overhaul plan moved the canonical implementation to
``src/splunk_uc/audits/compliance_gaps.py``; the dispatcher exposes it as
``python -m splunk_uc audit-compliance-gaps``.

This file remains as a thin shim so existing call sites continue to
work for the soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.compliance_gaps import (
    ASSURANCE_RANK,
    REGS_PATH,
    REPO_ROOT,
    REPORT_JSON,
    REPORT_MD,
    STATUS_MULTIPLIER,
    UC_SAMPLE_LIMIT,
    USE_CASES_DIR,
    ClauseEntry,
    ClauseGap,
    RegulationsCatalogue,
    RegVersion,
    UcComplianceHit,
    main,
)

__all__ = [
    "ASSURANCE_RANK",
    "REGS_PATH",
    "REPORT_JSON",
    "REPORT_MD",
    "REPO_ROOT",
    "STATUS_MULTIPLIER",
    "UC_SAMPLE_LIMIT",
    "USE_CASES_DIR",
    "ClauseEntry",
    "ClauseGap",
    "RegVersion",
    "RegulationsCatalogue",
    "UcComplianceHit",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
