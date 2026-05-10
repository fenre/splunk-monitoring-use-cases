#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.migrations.regenerate_cat22_ntv``.

The implementation moved under ``src/splunk_uc/migrations/`` as part
of the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 10,
standalone migrations cluster). This shim keeps the historic
``scripts/regenerate_cat22_ntv.py`` invocation alive while the new
dispatcher (``python -m splunk_uc regenerate-cat22-ntv``) becomes the
primary entry-point. The rendered ``"22": { ... }`` block must stay
byte-stable across releases for the CI drift guard (``--check``) to
remain truthful, so this shim is intentionally a thin re-export that
forwards ``main`` only -- the module-level constants
(``_OUTCOMES``, ``_AREAS``, ``BLOCK_START``) live exclusively in the
package implementation now.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.migrations.regenerate_cat22_ntv import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
