#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.migrations.migrate_compliance_phase4``.

The implementation moved under ``src/splunk_uc/migrations/`` as part
of the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 10,
standalone migrations cluster). This shim keeps the historic
``scripts/migrate_compliance_phase4.py`` invocation alive while the
new dispatcher (``python -m splunk_uc migrate-compliance-phase4``)
becomes the primary entry-point. The synthesised
controlObjective / evidenceArtifact strings must stay byte-stable
across releases for the CI drift guard (``--check``) to remain
truthful, so this shim is intentionally a thin re-export that
forwards ``main`` only -- the templating constants
(``SIDECAR_FIELD_ORDER``, ``COMPLIANCE_ENTRY_ORDER``) live exclusively
in the package implementation now.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.migrations.migrate_compliance_phase4 import main

__all__ = ["main"]


if __name__ == "__main__":
    sys.exit(main())
