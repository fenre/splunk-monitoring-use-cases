#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.legacy_orphans``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09. See
``docs/scripts-taxonomy.md`` for the migration recipe.

This shim keeps existing CI workflows, Makefile targets, and
maintainer ad-hoc invocations working unchanged during the soak
window. It re-exports the public CLI plus the module-level path
constants (``REPO_ROOT``, ``LEGACY_ROOT``, ``SSOT_ROOT``) and
helpers that the test suite monkeypatches or reads directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.legacy_orphans import (
    EXPECTED_ORPHAN_COUNT_AT_BASELINE,
    LEGACY_ROOT,
    REPO_ROOT,
    SSOT_ROOT,
    collect_legacy_ids,
    collect_orphan_titles,
    collect_ssot_ids,
    main,
    report,
)

__all__ = [
    "EXPECTED_ORPHAN_COUNT_AT_BASELINE",
    "LEGACY_ROOT",
    "REPO_ROOT",
    "SSOT_ROOT",
    "collect_legacy_ids",
    "collect_orphan_titles",
    "collect_ssot_ids",
    "main",
    "report",
]


if __name__ == "__main__":
    sys.exit(main())
