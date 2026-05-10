"""Compatibility shim — delegates to ``splunk_uc.ingest.manifest``.

The implementation moved under ``src/splunk_uc/ingest/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 8, ingest
cluster). This shim keeps the historic ``from manifest import ...``
imports inside ``scripts/ingest/ingest_*.py`` working unchanged during
the soak period — the legacy drivers inject ``scripts/ingest/`` onto
``sys.path`` so ``import manifest`` resolves to this file. The four
public names (``FetchRecord``, ``fetch``, ``write_manifest``,
``merge_into_manifest``) are re-exported so existing callers keep
working unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.ingest.manifest import (
    FetchRecord,
    fetch,
    merge_into_manifest,
    write_manifest,
)

__all__ = ["FetchRecord", "fetch", "merge_into_manifest", "write_manifest"]
