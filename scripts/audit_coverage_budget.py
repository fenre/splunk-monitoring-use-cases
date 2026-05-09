#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.coverage_budget``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09. See
``docs/scripts-taxonomy.md`` for the migration recipe.

This shim keeps existing CI workflows, Makefile targets, and
maintainer ad-hoc invocations working unchanged during the soak
window. It re-exports the public CLI plus the module-level path
constants and helpers that the test suite reads directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.coverage_budget import (
    REPO_ROOT,
    TIER_1_EXCLUDES,
    TIER_1_INCLUDES,
    TIER_2_INCLUDES,
    TIER_3_DOCUMENTED_EXEMPT,
    _build_arg_parser,
    _classify,
    _git_head,
    _load_coverage_report,
    _read_version,
    _short_record,
    build_baseline,
    check,
    main,
)

__all__ = [
    "REPO_ROOT",
    "TIER_1_EXCLUDES",
    "TIER_1_INCLUDES",
    "TIER_2_INCLUDES",
    "TIER_3_DOCUMENTED_EXEMPT",
    "_build_arg_parser",
    "_classify",
    "_git_head",
    "_load_coverage_report",
    "_read_version",
    "_short_record",
    "build_baseline",
    "check",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
