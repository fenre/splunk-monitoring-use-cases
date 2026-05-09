#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/splunkbase_ids.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-splunkbase-ids`` dispatcher. This
shim keeps the legacy ``python3 scripts/audit_splunkbase_ids.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.splunkbase_ids import (
    NEARBY_NAME_RE,
    REPO_ROOT,
    SPLUNKBASE_INLINE_RE,
    URL_RE,
    extract_refs,
    main,
    walk_files,
)

__all__ = [
    "NEARBY_NAME_RE",
    "REPO_ROOT",
    "SPLUNKBASE_INLINE_RE",
    "URL_RE",
    "extract_refs",
    "main",
    "walk_files",
]


if __name__ == "__main__":
    sys.exit(main())
