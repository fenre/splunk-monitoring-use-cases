#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.splunk_cloud_compat``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_splunk_cloud_compat.py`` invocation alive
while the new dispatcher (``python -m splunk_uc audit-splunk-cloud-compat``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.splunk_cloud_compat import (
    APP_DIRS,
    CATALOG_PATH_LEGACY,
    CATALOG_PATH_PRIMARY,
    DOC_OUT,
    JSON_OUT,
    PACK_RULES,
    REPO_ROOT,
    SPL_RULES,
    TA_DIR,
    Finding,
    PackRule,
    SplRule,
    audit_packs,
    audit_spl,
    main,
    render_report,
)

__all__ = [
    "APP_DIRS",
    "CATALOG_PATH_LEGACY",
    "CATALOG_PATH_PRIMARY",
    "DOC_OUT",
    "JSON_OUT",
    "PACK_RULES",
    "REPO_ROOT",
    "SPL_RULES",
    "TA_DIR",
    "Finding",
    "PackRule",
    "SplRule",
    "audit_packs",
    "audit_spl",
    "main",
    "render_report",
]


if __name__ == "__main__":
    sys.exit(main())
