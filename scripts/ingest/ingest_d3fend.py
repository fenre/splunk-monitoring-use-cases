#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.ingest.d3fend``.

The implementation moved under ``src/splunk_uc/ingest/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 8, ingest
cluster). This shim keeps the historic
``scripts/ingest/ingest_d3fend.py`` invocation alive while the new
dispatcher (``python -m splunk_uc ingest-d3fend``) becomes the
primary entry-point. The ``main`` and ``run`` symbols are re-exported
so the orchestrator (``scripts/ingest_all.py``) and any direct CLI
invocation in CI / maintainer notes still work unchanged during the
soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.ingest.d3fend import main, run

__all__ = ["main", "run"]


if __name__ == "__main__":
    sys.exit(main())
