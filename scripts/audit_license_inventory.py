#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.license_inventory``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.

This file used to be the ~960-line implementation. It was relocated
to ``src/splunk_uc/audits/license_inventory.py`` so the audit suite
is invokable through the unified ``python -m splunk_uc <verb>``
dispatcher.

The shim re-exports the public CLI ``main`` plus the module-level
constants and helpers exercised by ``tests/scripts/test_audit_license_inventory.py``
(``REPO_ROOT``, ``_PYPROJECT_FILES``, ``_INVENTORY_PATH``,
``_INVENTORY_MD_PATH``, ``build_inventory``, ``render_markdown``, plus
the pure-helper bench ``_split_requirement``, ``_normalise_license_string``,
``_extract_spdx_from_metadata``). The legacy ``scripts/...``
invocation is unchanged for ``make audit-license-inventory``,
``make write-license-inventory``, and any external documentation.

Once the v9.0 release ships and the new dispatcher path has had a
release of soak, the shim is a candidate for deletion; CI workflows
and Makefile targets will be cut over to ``python3 -m splunk_uc
audit-license-inventory`` in the same PR.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.license_inventory import (
    _INVENTORY_MD_PATH,
    _INVENTORY_PATH,
    _PYPROJECT_FILES,
    REPO_ROOT,
    _collect_declared_dependencies,
    _diff_inventories,
    _enumerate_vendored_licenses,
    _extract_spdx_from_metadata,
    _git_head,
    _identify_license_header,
    _is_inside_skip_dir,
    _is_license_filename,
    _md_cell,
    _MetadataLike,
    _normalise_distribution_name,
    _normalise_license_string,
    _read_pyproject,
    _read_repo_version,
    _read_top_license,
    _resolve_python_packages,
    _run_check,
    _run_print,
    _run_write,
    _split_requirement,
    _strip_volatile,
    _vendored_subject,
    _violations_against_allowlist,
    _write_inventory_json,
    build_inventory,
    main,
    render_markdown,
)

__all__ = [
    "REPO_ROOT",
    "_INVENTORY_MD_PATH",
    "_INVENTORY_PATH",
    "_PYPROJECT_FILES",
    "_MetadataLike",
    "_collect_declared_dependencies",
    "_diff_inventories",
    "_enumerate_vendored_licenses",
    "_extract_spdx_from_metadata",
    "_git_head",
    "_identify_license_header",
    "_is_inside_skip_dir",
    "_is_license_filename",
    "_md_cell",
    "_normalise_distribution_name",
    "_normalise_license_string",
    "_read_pyproject",
    "_read_repo_version",
    "_read_top_license",
    "_resolve_python_packages",
    "_run_check",
    "_run_print",
    "_run_write",
    "_split_requirement",
    "_strip_volatile",
    "_vendored_subject",
    "_violations_against_allowlist",
    "_write_inventory_json",
    "build_inventory",
    "main",
    "render_markdown",
]


if __name__ == "__main__":
    sys.exit(main())
