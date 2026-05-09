#!/usr/bin/env python3
"""Compatibility shim - the implementation lives in ``splunk_uc.audits.build_reproducibility``.

Repo-overhaul plan §P6 (scripts taxonomy), 2026-05-09.

This file used to be the ~210-line implementation. It was relocated
to ``src/splunk_uc/audits/build_reproducibility.py`` so the audit
suite is invokable through the unified ``python -m splunk_uc <verb>``
dispatcher.

The shim is kept (rather than deleted outright) so that:

* ``make audit-reproducibility`` and ``make audit-reproducibility-fast``
  keep working with their existing ``python3 scripts/...`` invocation.
* ``.github/workflows/build-reproducibility.yml`` and any external
  documentation that references the old path keep working through
  one release of soak time.
* Direct ad-hoc invocation by maintainers (``python3
  scripts/audit_build_reproducibility.py --first-build-only``) is
  unaffected.

The shim re-exports the module-level names that the existing test
suite (``tests/scripts/test_audit_build_reproducibility.py``)
patches, so no test changes are needed for the relocation. The
``main`` function is the same callable used by the dispatcher.

Once the v9.0 release ships and the new dispatcher path has had a
release of soak, the shim is a candidate for deletion; CI workflows
and Makefile targets will be cut over to ``python3 -m splunk_uc
audit-reproducibility`` in the same PR.
"""
from __future__ import annotations

import sys
from pathlib import Path

# The shim must keep working without ``pip install -e .`` because
# many maintainer workflows invoke it via the bare repo (CI, fresh
# clones, sandboxes). Add ``src/`` to sys.path on demand.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from splunk_uc.audits.build_reproducibility import (
    BUILD_SCRIPT,
    PROJECT_ROOT,
    _git_commit_epoch,
    _git_head_sha,
    _read_integrity,
    _run_build,
    main,
)

__all__ = [
    "BUILD_SCRIPT",
    "PROJECT_ROOT",
    "_git_commit_epoch",
    "_git_head_sha",
    "_read_integrity",
    "_run_build",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
