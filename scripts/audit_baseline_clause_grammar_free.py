#!/usr/bin/env python3
"""Phase F drift guard: assert the audit baseline carries no ``clause-grammar`` fingerprints.

Phase A of the regulation-coverage-gap plan drove the backlog of malformed
``compliance[].clause`` strings from 670 tolerated findings down to zero.
Phase F then removed ``clause-grammar`` from ``BASELINEABLE_CODES`` in
``scripts/audit_compliance_mappings.py`` so it can never again be recorded
in ``tests/golden/audit-baseline.json`` via ``--update-baseline``.

This script is the belt-and-braces CI guard for that invariant: even if a
future contributor accidentally re-adds ``clause-grammar`` to
``BASELINEABLE_CODES`` *and* runs ``--update-baseline`` on a branch,
``validate.yml`` will still reject the PR because this script walks the
baseline file and blocks on any ``clause-grammar`` fingerprint.

Fingerprints produced by
``scripts/audit_compliance_mappings.py::Finding.fingerprint`` are
tab-separated:

    <code>\t<uc_id>\t<path>\t<message>

Exit codes:
    0  invariant holds (no clause-grammar fingerprints in baseline)
    1  invariant violated, or baseline file missing / malformed
    2  unexpected I/O / parse error
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = REPO_ROOT / "tests" / "golden" / "audit-baseline.json"

# Phase F invariant: these codes must never appear in the baseline file.
FORBIDDEN_CODES = frozenset({"clause-grammar"})


def _is_forbidden(fp: str) -> bool:
    """Return True if ``fp`` carries one of the codes we refuse to baseline.

    Finding fingerprints are ``<code>\\t<uc_id>\\t<path>\\t<message>``.
    We only check the first field so we never accidentally match a
    ``clause-grammar`` substring that happens to appear inside a UC id
    or message of a different code.
    """
    code = fp.split("\t", 1)[0].strip()
    return code in FORBIDDEN_CODES


def main() -> int:
    if not BASELINE_PATH.is_file():
        print(
            f"::error::Phase F drift guard: expected baseline at "
            f"{BASELINE_PATH.relative_to(REPO_ROOT)} but it is missing.",
            file=sys.stderr,
        )
        return 1

    try:
        raw = BASELINE_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"::error::Phase F drift guard: cannot parse "
            f"{BASELINE_PATH.relative_to(REPO_ROOT)}: {exc}",
            file=sys.stderr,
        )
        return 2

    fingerprints = data.get("fingerprints", []) or []
    if not isinstance(fingerprints, list):
        print(
            "::error::Phase F drift guard: "
            f"{BASELINEABLE_FP_FIELD} must be a list, got {type(fingerprints).__name__}.",
            file=sys.stderr,
        )
        return 1

    offenders = [fp for fp in fingerprints if isinstance(fp, str) and _is_forbidden(fp)]

    if offenders:
        print(
            f"::error::Phase F invariant violated: "
            f"{len(offenders)} forbidden-code fingerprint(s) found in "
            f"{BASELINE_PATH.relative_to(REPO_ROOT)}.  These codes cannot "
            f"be baselined: {sorted(FORBIDDEN_CODES)}.  Fix the underlying "
            "issues instead of tolerating them.",
            file=sys.stderr,
        )
        for fp in offenders[:20]:
            print(f"  - {fp}", file=sys.stderr)
        if len(offenders) > 20:
            print(f"  … and {len(offenders) - 20} more.", file=sys.stderr)
        return 1

    print(
        f"Phase F invariant OK: 0 forbidden-code fingerprints in "
        f"{BASELINE_PATH.relative_to(REPO_ROOT)} "
        f"(total fingerprints: {len(fingerprints)}; "
        f"forbidden codes: {sorted(FORBIDDEN_CODES)})."
    )
    return 0


BASELINEABLE_FP_FIELD = "fingerprints"


if __name__ == "__main__":
    raise SystemExit(main())
