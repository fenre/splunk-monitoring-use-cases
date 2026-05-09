#!/usr/bin/env python3
"""Compatibility shim — implementation moved to ``splunk_uc.audits.oscal_roundtrip``.

This file is kept so legacy invocations of ``python3
scripts/audit_oscal_roundtrip.py`` and any in-tree imports of
``scripts.audit_oscal_roundtrip`` continue to work during the P6
migration soak window. It is a thin re-export of the public surface
of the canonical implementation under ``src/splunk_uc/audits/``.

New callers should use either:

* the dispatcher: ``python -m splunk_uc audit-oscal-roundtrip``
* the make target: ``make audit-oscal``

The shim will be deleted at the end of the P6 Tier 3 soak period
(see docs/scripts-taxonomy.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.oscal_roundtrip import (
    _FILENAME_RE,
    _UUID_RE,
    API_CDEF_DIR,
    CROSSWALK_DIR,
    EXPECTED_OSCAL_VERSION,
    MANIFEST_PATH,
    REPO,
    REPORT_PATH,
    SCHEMA_PATH,
    SCHEMA_SOURCE_ID,
    STATUS_BAD_FILENAME,
    STATUS_BAD_JSON,
    STATUS_MISSING_SOURCE,
    STATUS_OK,
    STATUS_ROUNDTRIP_DRIFT,
    STATUS_SCHEMA_VIOLATION,
    STATUS_WRONG_OSCAL_VERSION,
    _audit_file,
    _canonical_serialise,
    _collect_records,
    _extract_uc_id,
    _find_crosswalk_source,
    _load_schema,
    _print_human_summary,
    _render_report,
    _schema_meta,
    _schema_sha256_from_manifest,
    _schema_sha256_on_disk,
    main,
)

__all__ = [
    "API_CDEF_DIR",
    "CROSSWALK_DIR",
    "EXPECTED_OSCAL_VERSION",
    "MANIFEST_PATH",
    "REPO",
    "REPORT_PATH",
    "SCHEMA_PATH",
    "SCHEMA_SOURCE_ID",
    "STATUS_BAD_FILENAME",
    "STATUS_BAD_JSON",
    "STATUS_MISSING_SOURCE",
    "STATUS_OK",
    "STATUS_ROUNDTRIP_DRIFT",
    "STATUS_SCHEMA_VIOLATION",
    "STATUS_WRONG_OSCAL_VERSION",
    "_FILENAME_RE",
    "_UUID_RE",
    "_audit_file",
    "_canonical_serialise",
    "_collect_records",
    "_extract_uc_id",
    "_find_crosswalk_source",
    "_load_schema",
    "_print_human_summary",
    "_render_report",
    "_schema_meta",
    "_schema_sha256_from_manifest",
    "_schema_sha256_on_disk",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
