#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.dashboard_spl``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09. See
``docs/scripts-taxonomy.md`` for the migration recipe.

This shim keeps existing CI workflows, Makefile targets, and
maintainer ad-hoc invocations working unchanged during the soak
window. It re-exports the public CLI plus the dataclasses and
helpers that the test suite reads and instantiates directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.dashboard_spl import (
    AuditResult,
    Panel,
    Splunkd,
    TokenSpec,
    _collect_panels,
    _expand_tokens,
    _parse_inputs,
    _resolve_token,
    _strip_ns,
    main,
)

__all__ = [
    "AuditResult",
    "Panel",
    "Splunkd",
    "TokenSpec",
    "_collect_panels",
    "_expand_tokens",
    "_parse_inputs",
    "_resolve_token",
    "_strip_ns",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
