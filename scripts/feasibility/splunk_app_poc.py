#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.feasibility.splunk_app_poc``.

The implementation moved under ``src/splunk_uc/feasibility/`` as part
of the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 9,
feasibility cluster). This shim keeps the historic
``scripts/feasibility/splunk_app_poc.py`` invocation alive while the
new dispatcher (``python -m splunk_uc feasibility-splunk-app-poc``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.feasibility.splunk_app_poc import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
