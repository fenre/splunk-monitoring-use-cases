#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.generators.mapping_ledger``.

The implementation moved under ``src/splunk_uc/generators/`` as part of
the Phase 6 scripts taxonomy reorganisation (Tier 2 batch 1, generator
half). This shim keeps the historic
``scripts/generate_mapping_ledger.py`` invocation alive while the new
dispatcher (``python -m splunk_uc generate-mapping-ledger``) becomes the
primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.generators.mapping_ledger import (
    AUXILIARY_SOURCES,
    CANONICAL_ALGORITHM,
    CANONICAL_FIELD_ORDER,
    CANONICAL_JSON_FORM,
    CONTENT_DIR,
    HASH_ALGORITHM,
    LEDGER_PATH,
    REGULATIONS_JSON,
    ROOT,
    SCHEMA_VERSION,
    SIGNOFFS_DIR,
    USE_CASES_DIR,
    LedgerInput,
    build_auxiliary_sources,
    build_ledger,
    build_ledger_entry,
    build_ledger_inputs,
    canonical_dump,
    canonical_entry_payload,
    catalogue_head_commit,
    commit_date_iso,
    compute_merkle_root,
    deterministic_generated_at,
    git_first_seen_commit,
    git_last_modified_commit,
    iter_uc_sidecars,
    load_regulation_index,
    load_signoffs,
    main,
    mapping_id_of,
    normalise_version,
    render,
    resolve_regulation_id,
    sha256_hex,
    signoff_status_for,
)

__all__ = [
    "AUXILIARY_SOURCES",
    "CANONICAL_ALGORITHM",
    "CANONICAL_FIELD_ORDER",
    "CANONICAL_JSON_FORM",
    "CONTENT_DIR",
    "HASH_ALGORITHM",
    "LEDGER_PATH",
    "REGULATIONS_JSON",
    "ROOT",
    "SCHEMA_VERSION",
    "SIGNOFFS_DIR",
    "USE_CASES_DIR",
    "LedgerInput",
    "build_auxiliary_sources",
    "build_ledger",
    "build_ledger_entry",
    "build_ledger_inputs",
    "canonical_dump",
    "canonical_entry_payload",
    "catalogue_head_commit",
    "commit_date_iso",
    "compute_merkle_root",
    "deterministic_generated_at",
    "git_first_seen_commit",
    "git_last_modified_commit",
    "iter_uc_sidecars",
    "load_regulation_index",
    "load_signoffs",
    "main",
    "mapping_id_of",
    "normalise_version",
    "render",
    "resolve_regulation_id",
    "sha256_hex",
    "signoff_status_for",
]


if __name__ == "__main__":
    sys.exit(main())
