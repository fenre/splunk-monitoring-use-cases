#!/usr/bin/env python3
"""Compatibility shim — delegates to ``splunk_uc.audits.mapping_ledger``.

The implementation moved under ``src/splunk_uc/audits/`` as part of
the Phase 6 scripts taxonomy reorganisation. This shim keeps the
historic ``scripts/audit_mapping_ledger.py`` invocation alive while
the new dispatcher (``python -m splunk_uc audit-mapping-ledger``)
becomes the primary entry-point.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.mapping_ledger import (
    LEDGER_PATH,
    REPORT_PATH,
    ROOT,
    SCHEMA_PATH,
    audit_catalogue_commit,
    audit_entry_count,
    audit_entry_hashes,
    audit_merkle_root,
    audit_referential_integrity,
    audit_signature_envelope,
    audit_sort_order,
    gather_sidecar_mappings,
    main,
    validate_schema,
    write_report,
)

__all__ = [
    "LEDGER_PATH",
    "REPORT_PATH",
    "ROOT",
    "SCHEMA_PATH",
    "audit_catalogue_commit",
    "audit_entry_count",
    "audit_entry_hashes",
    "audit_merkle_root",
    "audit_referential_integrity",
    "audit_signature_envelope",
    "audit_sort_order",
    "gather_sidecar_mappings",
    "main",
    "validate_schema",
    "write_report",
]


if __name__ == "__main__":
    sys.exit(main())
