#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/changelog_uc_refs.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-changelog-uc-refs`` dispatcher.
This shim keeps the legacy ``python3 scripts/audit_changelog_uc_refs.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.changelog_uc_refs import (
    CHANGELOG,
    HEADER_RE,
    REPO,
    UC_HEADER_RE,
    UC_REF_RE,
    USE_CASES,
    ChangelogEntry,
    collect_uc_definitions,
    main,
    parse_changelog,
    validate_changelog,
    validate_uc_refs,
)

__all__ = [
    "CHANGELOG",
    "HEADER_RE",
    "REPO",
    "UC_HEADER_RE",
    "UC_REF_RE",
    "USE_CASES",
    "ChangelogEntry",
    "collect_uc_definitions",
    "main",
    "parse_changelog",
    "validate_changelog",
    "validate_uc_refs",
]


if __name__ == "__main__":
    sys.exit(main())
