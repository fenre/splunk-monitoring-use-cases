#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.tools.validate_uc_schema_staged``.

The implementation moved under ``src/splunk_uc/tools/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 11,
recurring-tools cluster). This shim keeps the historic
``scripts/validate_uc_schema_staged.py`` invocation alive for the
existing ``.pre-commit-config.yaml`` hook entry (which passes a list
of staged UC JSON file paths after the program name) while the new
dispatcher (``python -m splunk_uc validate-uc-schema-staged``)
becomes the primary entry-point. The shim slices off the legacy
``argv[0]`` program-name slot to match the dispatcher contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.tools.validate_uc_schema_staged import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
