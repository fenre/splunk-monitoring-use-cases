#!/usr/bin/env python3
"""Audit every UC's compliance[] mappings against the regulations catalogue (legacy shim).

Phase 6 of the repo overhaul plan moved the canonical implementation to
``src/splunk_uc/audits/compliance_mappings.py``; the dispatcher exposes it as
``python -m splunk_uc audit-compliance-mappings``.

This file remains as a thin shim so existing call sites continue to
work for the soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.compliance_mappings import (
    ASSURANCE_MULTIPLIER,
    ASSURANCE_RANK,
    BASELINE_PATH,
    BASELINEABLE_CODES,
    GOLDEN_PATH,
    REGS_PATH,
    REPO_ROOT,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_PATH,
    STATUS_CAP,
    UC_GLOB,
    AuditState,
    ComplianceEntry,
    Finding,
    Metrics,
    RegulationsCatalogue,
    RegVersion,
    ResolvedRef,
    main,
)

__all__ = [
    "ASSURANCE_MULTIPLIER",
    "ASSURANCE_RANK",
    "BASELINEABLE_CODES",
    "BASELINE_PATH",
    "GOLDEN_PATH",
    "REGS_PATH",
    "REPORT_JSON",
    "REPORT_MD",
    "REPO_ROOT",
    "SCHEMA_PATH",
    "STATUS_CAP",
    "UC_GLOB",
    "AuditState",
    "ComplianceEntry",
    "Finding",
    "Metrics",
    "RegVersion",
    "RegulationsCatalogue",
    "ResolvedRef",
    "main",
]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:  # pragma: no cover
        import traceback

        traceback.print_exc()
        raise SystemExit(2) from None
