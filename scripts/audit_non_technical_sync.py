#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/non_technical_sync.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-non-technical-sync`` dispatcher.
This shim keeps the legacy ``python3 scripts/audit_non_technical_sync.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.non_technical_sync import (
    JS_PATH,
    RE_ID,
    RE_SUBCAT,
    RE_UC_HEADER,
    REPO,
    USE_CASES,
    extract_top_level_string_keys,
    main,
    parse_js_category_blocks,
)

__all__ = [
    "JS_PATH",
    "REPO",
    "RE_ID",
    "RE_SUBCAT",
    "RE_UC_HEADER",
    "USE_CASES",
    "extract_top_level_string_keys",
    "main",
    "parse_js_category_blocks",
]


if __name__ == "__main__":
    sys.exit(main())
