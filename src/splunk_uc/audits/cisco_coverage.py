"""Ratchet gate for Cisco portfolio coverage.

Builds the same matrix as ``generate-cisco-coverage`` and fails when:

- a UC names a capability that is not in ``data/cisco-portfolio.json``;
- an observable capability is uncovered, or lacks a CIM-backed UC where
  the capability declares CIM models, and the gap is neither waived nor
  in the recorded backlog;
- a product has no tagged UC and is not in the recorded backlog;
- a waiver has no reason or names an unknown capability;
- a backlog entry is now closed (the ratchet only tightens: remove it
  with ``--write-baseline``).

Waivers live in ``data/cisco-coverage-baseline.json`` under ``waivers``
and are kept by ``--write-baseline``, as are ``emptyProductNotes``.
``pendingGaps`` and ``emptyProducts`` are rewritten from the current state.

Subcategory outcomes are enforced by ``audit-non-technical-sync``, which
requires every subcategory to have an entry in ``non-technical-view.js``.

Usage::

    python -m splunk_uc audit-cisco-coverage --check
    python -m splunk_uc audit-cisco-coverage --write-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from splunk_uc.generators import cisco_coverage as cov

BASELINE = cov.REPO / "data" / "cisco-coverage-baseline.json"
GAP_STATUSES = (cov.STATUS_UNCOVERED, cov.STATUS_CIM_GAP)


def _gap_key(gap: dict[str, Any]) -> str:
    return f"{gap['capability']}:{gap['status']}"


def load_baseline(path: Path = BASELINE) -> dict[str, Any]:
    if not path.exists():
        return {"waivers": [], "pendingGaps": [], "emptyProducts": []}
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return data


def evaluate(matrix: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    known = {c["ref"] for p in matrix["products"] for c in p["capabilities"]}

    for u in matrix["unknownCapabilityRefs"]:
        errors.append(f"{u['useCase']}: unknown capability `{u['capability']}` (not in data/cisco-portfolio.json)")

    waived: set[str] = set()
    for w in baseline.get("waivers", []):
        ref = w.get("capability", "")
        if ref not in known:
            errors.append(f"waiver for unknown capability `{ref}`")
        if not str(w.get("reason", "")).strip():
            errors.append(f"waiver for `{ref}` has no reason")
        waived.add(ref)

    pending = set(baseline.get("pendingGaps", []))
    current = {_gap_key(g) for g in matrix["gaps"] if g["capability"] not in waived}
    for key in sorted(current - pending):
        errors.append(f"new coverage gap `{key}`: author a UC, or add a waiver with a reason")
    for key in sorted(pending - current):
        errors.append(f"backlog entry `{key}` is closed: run `audit-cisco-coverage --write-baseline` to ratchet")

    empty_now = {p["slug"] for p in matrix["products"] if not p["useCaseCount"]}
    empty_base = set(baseline.get("emptyProducts", []))
    for slug in sorted(empty_now - empty_base):
        errors.append(f"product `{slug}` has no tagged use cases and is not in the backlog")
    for slug in sorted(empty_base - empty_now):
        errors.append(f"product `{slug}` now has use cases: run `audit-cisco-coverage --write-baseline` to ratchet")
    return errors


def write_baseline(matrix: dict[str, Any], baseline: dict[str, Any], path: Path = BASELINE) -> None:
    waivers = sorted(baseline.get("waivers", []), key=lambda w: w.get("capability", ""))
    waived = {w.get("capability") for w in waivers}
    out = {
        "$comment": (
            "Ratchet baseline for `python -m splunk_uc audit-cisco-coverage`. "
            "`waivers` are hand-curated (capability + reason) and preserved, "
            "as are `emptyProductNotes`; "
            "`pendingGaps` and `emptyProducts` are rewritten by --write-baseline and may only shrink."
        ),
        "waivers": waivers,
        "pendingGaps": sorted(_gap_key(g) for g in matrix["gaps"] if g["capability"] not in waived),
        "emptyProducts": sorted(p["slug"] for p in matrix["products"] if not p["useCaseCount"]),
    }
    notes = baseline.get("emptyProductNotes") or []
    if notes:
        out["emptyProductNotes"] = notes
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit-cisco-coverage", description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Exit 1 on any violation (default).")
    mode.add_argument("--write-baseline", action="store_true", help="Rewrite pendingGaps and emptyProducts.")
    args = parser.parse_args(argv)

    matrix = cov.build_matrix(cov.load_portfolio(), cov.collect_ucs())
    baseline = load_baseline()
    if args.write_baseline:
        if matrix["unknownCapabilityRefs"]:
            for line in evaluate(matrix, {"waivers": baseline.get("waivers", [])}):
                if "unknown capability" in line:
                    print(f"FAIL: {line}", file=sys.stderr)
            return 1
        write_baseline(matrix, baseline)
        print(f"wrote {BASELINE.relative_to(cov.REPO)}")
        return 0

    errors = evaluate(matrix, baseline)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    s = matrix["summary"]
    print(
        f"OK: {s['coveredCapabilities']}/{s['observableCapabilities']} observable Cisco capabilities covered, "
        f"{len(baseline.get('pendingGaps', []))} in backlog, {len(baseline.get('waivers', []))} waived."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
