#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.recommender_app``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 5, recommender
app cluster). This shim keeps the historic
``scripts/generate_recommender_app.py`` invocation alive while the new
dispatcher (``python -m splunk_uc generate-recommender-app``) becomes
the primary entry-point. The ``main`` symbol is re-exported so existing
callers (``tests/build/test_scripts.py``,
``.github/workflows/validate.yml``,
``.github/workflows/release.yml``) keep working unchanged during the
soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.recommender_app import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
