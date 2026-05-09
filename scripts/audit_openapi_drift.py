#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.openapi_drift``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_openapi_drift.py`` invocation alive while the
new dispatcher (``python -m splunk_uc audit-openapi-drift``) becomes
the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.openapi_drift import (
    PROJECT_ROOT,
    collect_dist_paths,
    load_yaml_paths,
    main,
)

__all__ = [
    "PROJECT_ROOT",
    "collect_dist_paths",
    "load_yaml_paths",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
