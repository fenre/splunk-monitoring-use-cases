#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.tools.inventory_ucs``.

The implementation moved under ``src/splunk_uc/tools/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 11,
recurring-tools cluster). This shim keeps the historic
``scripts/inventory_ucs.py`` invocation alive while the new
dispatcher (``python -m splunk_uc inventory-ucs``) becomes the
primary entry-point. The emitted ``data/inventory/ucs.json``
deliberately keeps its legacy ``generatedAtComment`` for byte
stability during the soak; that string will be refreshed in a
later PR alongside the rest of the soaked-shim retirement.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.tools.inventory_ucs import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
