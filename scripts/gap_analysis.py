#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.migrations.gap_analysis``.

The implementation moved under ``src/splunk_uc/migrations/`` as part
of the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 10,
standalone migrations cluster). This shim keeps the historic
``scripts/gap_analysis.py`` invocation alive while the new dispatcher
(``python -m splunk_uc gap-analysis``) becomes the primary
entry-point. The verb name has no ``migrate-`` prefix because this
is a reporting tool (correlates inventory with regulations) rather
than a sidecar mutation; the committed
``data/inventory/gap-analysis.json`` already references this name in
its ``generatedComment``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.migrations.gap_analysis import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
