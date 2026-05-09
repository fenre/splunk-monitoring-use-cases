#!/usr/bin/env python3
"""Compatibility shim — implementation moved to ``splunk_uc.audits.regulatory_change_watch``.

This file is kept so legacy invocations of ``python3
scripts/audit_regulatory_change_watch.py`` and any in-tree imports of
``scripts.audit_regulatory_change_watch`` continue to work during the
P6 migration soak window. It is a thin re-export of the public surface
of the canonical implementation under ``src/splunk_uc/audits/``.

New callers should use either:

* the dispatcher: ``python -m splunk_uc audit-regulatory-change-watch``
* the make target: ``make audit-regulatory-change-watch``

The shim will be deleted at the end of the P6 Tier 3 soak period
(see docs/scripts-taxonomy.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.regulatory_change_watch import (
    HTTP_TIMEOUT_SECONDS,
    INGEST_PATH,
    REGULATIONS_PATH,
    REPO_ROOT,
    REPORT_PATH,
    SCHEMA_PATH,
    USER_AGENT,
    WATCH_PATH,
    cmd_check,
    cmd_fetch,
    cmd_freeze,
    main,
)

__all__ = [
    "HTTP_TIMEOUT_SECONDS",
    "INGEST_PATH",
    "REGULATIONS_PATH",
    "REPORT_PATH",
    "REPO_ROOT",
    "SCHEMA_PATH",
    "USER_AGENT",
    "WATCH_PATH",
    "cmd_check",
    "cmd_fetch",
    "cmd_freeze",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
