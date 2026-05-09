#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/links.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-links`` dispatcher. This shim
keeps the legacy ``python3 scripts/audit_links.py`` invocation working
unchanged for Makefile/CI/docs callers during the soak period; once
external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.links import (
    BROWSER_UA,
    HEAD_FALLBACK_CODES,
    IGNORE_FILE,
    MAX_WORKERS,
    PER_HOST_DELAY_SEC,
    RATE_LIMIT_CODES,
    REFERENCES_LINE,
    REPO_ROOT,
    RETRY_AFTER_DEFAULT,
    TIMEOUT_SEC,
    URL_PATTERN,
    check_url,
    collect_urls,
    load_ignore_patterns,
    main,
    normalize_url,
)

__all__ = [
    "BROWSER_UA",
    "HEAD_FALLBACK_CODES",
    "IGNORE_FILE",
    "MAX_WORKERS",
    "PER_HOST_DELAY_SEC",
    "RATE_LIMIT_CODES",
    "REFERENCES_LINE",
    "REPO_ROOT",
    "RETRY_AFTER_DEFAULT",
    "TIMEOUT_SEC",
    "URL_PATTERN",
    "check_url",
    "collect_urls",
    "load_ignore_patterns",
    "main",
    "normalize_url",
]


if __name__ == "__main__":
    sys.exit(main())
