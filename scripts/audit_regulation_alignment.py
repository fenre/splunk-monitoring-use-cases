#!/usr/bin/env python3
"""Compatibility shim — implementation moved to ``splunk_uc.audits.regulation_alignment``.

This file is kept so legacy invocations of ``python3
scripts/audit_regulation_alignment.py`` and any in-tree imports of
``scripts.audit_regulation_alignment`` continue to work during the P6
migration soak window. It is a thin re-export of the public surface of
the canonical implementation under ``src/splunk_uc/audits/``.

New callers should use either:

* the dispatcher: ``python -m splunk_uc audit-regulation-alignment``
* the make target: ``make audit-regulation-alignment``

The shim will be deleted at the end of the P6 Tier 3 soak period
(see docs/scripts-taxonomy.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.regulation_alignment import (
    REPO,
    _lower_to_canon,
    main,
)

__all__ = [
    "REPO",
    "_lower_to_canon",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
