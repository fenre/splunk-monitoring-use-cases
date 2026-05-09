#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.roadmap_consistency``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.

This file used to be the ~650-line implementation. It was relocated
to ``src/splunk_uc/audits/roadmap_consistency.py`` so the audit
suite is invokable through the unified ``python -m splunk_uc <verb>``
dispatcher.

The shim is kept (rather than deleted outright) so that:

* ``make audit-roadmap`` and ``make export-roadmap`` keep working
  with their existing ``python3 scripts/...`` invocation when the
  ``SPLUNK_UC`` macro is overridden.
* External documentation that references the old path (release notes,
  blog posts, migration guides) keeps working through one release
  of soak time.
* Direct ad-hoc invocation by maintainers (``python3
  scripts/audit_roadmap_consistency.py --check``) is unaffected.

The shim re-exports the module-level names that the existing test
suite (``tests/scripts/test_audit_roadmap_consistency.py``) loads
via ``importlib.util.spec_from_file_location`` plus the names that
test code monkeypatches (``VERSION_FILE``, ``CHANGELOG_MD``).

Once the v9.0 release ships and the new dispatcher path has had a
release of soak, the shim is a candidate for deletion; CI workflows
and Makefile targets will be cut over to ``python3 -m splunk_uc
audit-roadmap-consistency`` in the same PR.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.roadmap_consistency import (
    CHANGELOG_MD,
    REPO_ROOT,
    ROADMAP_MD,
    SCHEMA_VERSION,
    VERSION_FILE,
    _check_links,
    _extract_next_up_version,
    _extract_release_entries,
    _git_head,
    _Issue,
    _join_multiline_bullets,
    _next_up_heading,
    _read_version_triple,
    _ReleaseEntry,
    _Snapshot,
    _snapshot_to_dict,
    _split_sections,
    _versions_compatible,
    check_version_triple,
    main,
    parse_roadmap,
)

__all__ = [
    "CHANGELOG_MD",
    "REPO_ROOT",
    "ROADMAP_MD",
    "SCHEMA_VERSION",
    "VERSION_FILE",
    "_Issue",
    "_ReleaseEntry",
    "_Snapshot",
    "_check_links",
    "_extract_next_up_version",
    "_extract_release_entries",
    "_git_head",
    "_join_multiline_bullets",
    "_next_up_heading",
    "_read_version_triple",
    "_snapshot_to_dict",
    "_split_sections",
    "_versions_compatible",
    "check_version_triple",
    "main",
    "parse_roadmap",
]


if __name__ == "__main__":
    sys.exit(main())
