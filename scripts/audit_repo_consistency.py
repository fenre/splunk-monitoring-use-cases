#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/repo_consistency.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-repo-consistency`` dispatcher.
This shim keeps the legacy ``python3 scripts/audit_repo_consistency.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.repo_consistency import (
    EXPECTED_CATS,
    INDEX_HTML,
    INDEX_PATH,
    RE_CAT_HEADER,
    RE_ICON,
    RE_STARTER,
    REPO_ROOT,
    REQUIRED_SPLUNK_APP_KEYS,
    UC_DIR,
    extract_build_assignments,
    main,
    parse_index,
    parse_si_paths_keys,
)

__all__ = [
    "EXPECTED_CATS",
    "INDEX_HTML",
    "INDEX_PATH",
    "REPO_ROOT",
    "REQUIRED_SPLUNK_APP_KEYS",
    "RE_CAT_HEADER",
    "RE_ICON",
    "RE_STARTER",
    "UC_DIR",
    "extract_build_assignments",
    "main",
    "parse_index",
    "parse_si_paths_keys",
]


if __name__ == "__main__":
    sys.exit(main())
