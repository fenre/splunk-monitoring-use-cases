#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.stewardship_digest``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 1, generator
half). This shim keeps the historic
``scripts/generate_stewardship_digest.py`` invocation alive while the
new dispatcher (``python -m splunk_uc generate-stewardship-digest``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.stewardship_digest import (
    COVERAGE_AXES,
    DEFAULT_CONTENT,
    DEFAULT_HISTORY,
    DEFAULT_METRICS,
    DEFAULT_OUT,
    DEFAULT_STALE_THRESHOLD_DAYS,
    LEADER_AXES,
    LEADER_NAME_KEYS,
    PROJECT_ROOT,
    SCHEMA_REF,
    SCHEMA_VERSION,
    TOP_MOVERS_LIMIT,
    TOP_STALE_LIMIT,
    build_digest,
    main,
    render_markdown,
)

__all__ = [
    "COVERAGE_AXES",
    "DEFAULT_CONTENT",
    "DEFAULT_HISTORY",
    "DEFAULT_METRICS",
    "DEFAULT_OUT",
    "DEFAULT_STALE_THRESHOLD_DAYS",
    "LEADER_AXES",
    "LEADER_NAME_KEYS",
    "PROJECT_ROOT",
    "SCHEMA_REF",
    "SCHEMA_VERSION",
    "TOP_MOVERS_LIMIT",
    "TOP_STALE_LIMIT",
    "build_digest",
    "main",
    "render_markdown",
]


if __name__ == "__main__":
    sys.exit(main())
