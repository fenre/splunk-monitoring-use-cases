#!/usr/bin/env python3
"""Compatibility shim. Implementation lives in
``src/splunk_uc/audits/guide_xrefs.py``.

Batch 12 (2026-05-09): created the audit so the broken-link cleanup
landed alongside a permanent regression guard. The shim keeps the
``python3 scripts/audit_guide_xrefs.py`` invocation working for
Makefile/CI/docs callers; the canonical entry point is
``python -m splunk_uc audit-guide-xrefs``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.guide_xrefs import (
    GUIDES_DIR,
    LINK_RE,
    REPO_ROOT,
    SCRIPT_DIR,
    BrokenLink,
    _is_guide_target,
    collect_broken_links,
    main,
)

__all__ = [
    "GUIDES_DIR",
    "LINK_RE",
    "REPO_ROOT",
    "SCRIPT_DIR",
    "BrokenLink",
    "_is_guide_target",
    "collect_broken_links",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
