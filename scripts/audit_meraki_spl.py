#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.meraki_spl``.

The implementation moved under ``src/splunk_uc/audits/`` as part of the
Phase 6 scripts taxonomy reorganisation (Tier 1 batch 12, the trailing
audit body that was missed by the earlier "Tier 1 audit migration
COMPLETE" claim — see the Tier 1 batch 11 entry in
``docs/migration-status.md``). This shim keeps the historic
``scripts/audit_meraki_spl.py`` invocation alive while the new
dispatcher (``python -m splunk_uc audit-meraki-spl``) becomes the
primary entry-point. The ``main`` symbol is re-exported so any direct
CLI invocation in maintainer notes keeps working unchanged during the
soak period.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.meraki_spl import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
