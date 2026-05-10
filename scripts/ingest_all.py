#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.ingest.run_all``.

The implementation moved under ``src/splunk_uc/ingest/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 8, ingest
cluster). This shim keeps the historic ``scripts/ingest_all.py``
invocation alive while the new dispatcher (``python -m splunk_uc
ingest-all``) becomes the primary entry-point. The ``main`` symbol is
re-exported so any direct CLI invocation in CI / maintainer notes
still works unchanged during the soak period.

Implementation note: the new module is ``splunk_uc.ingest.run_all``
rather than ``splunk_uc.ingest.all`` because ``all`` shadows the
Python built-in.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.ingest.run_all import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
