#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in ``src/splunk_uc/audits/design_doc_freshness.py``.

P6 (scripts taxonomy, 2026-05-09): the canonical implementation moved
into the ``splunk_uc`` package so it can be invoked through the
unified ``python -m splunk_uc audit-design-doc-freshness`` dispatcher.
This shim keeps the legacy ``python3 scripts/audit_design_doc_freshness.py``
invocation working unchanged for Makefile/CI/docs callers during the
soak period; once external callers have migrated this file is deleted.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.design_doc_freshness import (
    CANONICAL_SECTIONS,
    DESIGN_MD,
    LINK_RE,
    REPO_ROOT,
    SCRIPT_DIR,
    extract_h2_sections,
    main,
    read_design,
    resolve_link,
)

__all__ = [
    "CANONICAL_SECTIONS",
    "DESIGN_MD",
    "LINK_RE",
    "REPO_ROOT",
    "SCRIPT_DIR",
    "extract_h2_sections",
    "main",
    "read_design",
    "resolve_link",
]


if __name__ == "__main__":
    sys.exit(main())
