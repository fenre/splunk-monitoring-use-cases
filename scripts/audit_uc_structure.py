#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.uc_structure``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09. See
``docs/scripts-taxonomy.md`` for the migration recipe.

This shim keeps existing CI workflows, Makefile targets, and
maintainer ad-hoc invocations working unchanged during the soak
window. It re-exports the public CLI plus the module-level path
constants, regex/field tables, and validators that the test
suite reads directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.uc_structure import (
    CONTENT,
    JSON_FIELDS_ALLOW_EMPTY_LIST,
    LARGE_THRESHOLD,
    RE_FIELD_LINE,
    RE_SPL_MARKER,
    RE_UC_HEAD,
    REPO_ROOT,
    REQUIRED_FIELDS,
    REQUIRED_JSON_FIELDS,
    SAMPLE_SIZE,
    USE_CASES,
    VALID_CRITICALITY,
    VALID_CRITICALITY_JSON,
    VALID_DIFFICULTY,
    VALID_DIFFICULTY_JSON,
    UCParse,
    _audit_json_corpus,
    _audit_markdown,
    _load_baseline,
    audit_uc,
    audit_uc_json,
    extract_field_lines,
    extract_spl_fenced,
    main,
    split_uc_blocks,
)

__all__ = [
    "CONTENT",
    "JSON_FIELDS_ALLOW_EMPTY_LIST",
    "LARGE_THRESHOLD",
    "REPO_ROOT",
    "REQUIRED_FIELDS",
    "REQUIRED_JSON_FIELDS",
    "RE_FIELD_LINE",
    "RE_SPL_MARKER",
    "RE_UC_HEAD",
    "SAMPLE_SIZE",
    "USE_CASES",
    "VALID_CRITICALITY",
    "VALID_CRITICALITY_JSON",
    "VALID_DIFFICULTY",
    "VALID_DIFFICULTY_JSON",
    "UCParse",
    "_audit_json_corpus",
    "_audit_markdown",
    "_load_baseline",
    "audit_uc",
    "audit_uc_json",
    "extract_field_lines",
    "extract_spl_fenced",
    "main",
    "split_uc_blocks",
]


if __name__ == "__main__":
    sys.exit(main())
