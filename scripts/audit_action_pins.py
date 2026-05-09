#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.action_pins``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09. See
``docs/scripts-taxonomy.md`` for the migration recipe.

This shim keeps existing CI workflows, Makefile targets, and
maintainer ad-hoc invocations working unchanged during the soak
window. It re-exports the public CLI plus the helpers and the
``_TransientError`` exception that the test suite raises and
catches against.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.action_pins import (
    _TransientError,
    collect_pins,
    main,
    resolve_tag_sha,
    to_owner_repo,
)

__all__ = [
    "_TransientError",
    "collect_pins",
    "main",
    "resolve_tag_sha",
    "to_owner_repo",
]


if __name__ == "__main__":
    sys.exit(main())
