#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.splunkbase_mappings``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 6, generators
finalisation). This shim keeps the historic
``scripts/generate_splunkbase_mappings.py`` invocation alive while the
new dispatcher (``python -m splunk_uc generate-splunkbase-mappings``)
becomes the primary entry-point. The ``main`` symbol is re-exported so
the docstring references in ``scripts/sync_splunkbase_catalog.py`` and
``scripts/review_splunkbase_mappings.py``, and any direct CLI
invocation in maintainer notes, keep working unchanged during the soak
period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.splunkbase_mappings import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
