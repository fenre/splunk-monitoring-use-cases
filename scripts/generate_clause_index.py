#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.clause_index``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 4, auxiliary
content + dashboard cluster). This shim keeps the historic
``scripts/generate_clause_index.py`` invocation alive while the new
dispatcher (``python -m splunk_uc generate-clause-index``) becomes the
primary entry-point. The ``generate`` symbol is also re-exported so
existing callers (such as ``generate_api_surface``) keep working
unchanged during the soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.clause_index import generate, main

__all__ = ["generate", "main"]


if __name__ == "__main__":
    sys.exit(main())
