#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.tools.extract_release_notes``.

The implementation moved under ``src/splunk_uc/tools/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 11,
recurring-tools cluster). This shim keeps the historic
``scripts/extract_release_notes.py`` invocation alive while the new
dispatcher (``python -m splunk_uc extract-release-notes``) becomes
the primary entry-point. The release workflow under
``.github/workflows/release.yml`` and any human re-runs of historic
documentation links continue to work unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.tools.extract_release_notes import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
