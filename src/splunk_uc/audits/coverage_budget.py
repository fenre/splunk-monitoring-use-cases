#!/usr/bin/env python3
"""Coverage budget auditor.

Repo-overhaul plan §P16 (2026-05-09): test coverage in this
repository is uneven by design. The build-pipeline core
(``tools/build/``) sits at 49.5% line coverage and has every right
to be in the high-90s eventually; the auditing CLIs (``scripts/audit_*.py``)
sit anywhere from 0% to 72% depending on how much in-process testing
was practical at the time of authorship; the one-shot migration / uplift
helpers (``scripts/uplift_*.py``, ``scripts/migrate_*.py``,
``scripts/_*.py``) are intentionally untested because they ran once,
edited the catalogue, and were retired.

This auditor pins a *baseline* of per-file coverage from a known-good
build (v9.1.0 is the inaugural snapshot) and rejects any PR that
regresses tier-1 or tier-2 coverage by more than a configurable
tolerance (default 1.0 percentage points). It is the burndown
mechanism described in §P16:

* Tier 1 (``tools/build/``): the build pipeline core. New code must
  not drop the per-file percent_covered below ``baseline - tolerance``.
  New files must hit ``--tier1-floor`` (default 60%).
* Tier 2 (``scripts/audit_*.py``, plus the named exceptions in
  ``TIER_2_INCLUDES``): audit CLIs that run in CI. Same ratchet rule;
  new-file floor at ``--tier2-floor`` (default 40%).
* Tier 3 (everything else under ``scripts/``): one-shot helpers —
  not gated.

Why a ratchet rather than a hard floor
--------------------------------------

The repository started with 11% line coverage; a hard 80% floor
would have forced an unattainable burndown sprint and pushed
contributors to test-only-the-easy-bits. A ratchet lets coverage
rise organically: every PR that adds tests improves the baseline;
every PR that adds code without tests fails the ratchet. The
baseline is regenerated at each minor release and committed under
``data/baselines/coverage-vX.Y.Z.json``.

Baseline regeneration
---------------------

::

    python3 scripts/audit_coverage_budget.py --print-baseline > data/baselines/coverage-vX.Y.Z.json

The baseline JSON captures version, capture timestamp, git HEAD, the
total-line rollup, and per-file coverage for tier-1 + tier-2 files.
Tier-3 files are listed under ``tier_3_exempt`` so the schema is
explicit about what's *not* gated.

Usage
-----

CI (default — just check, no print):

::

    python3 scripts/audit_coverage_budget.py \\
        --baseline data/baselines/coverage-v9.1.0.json \\
        --report /tmp/coverage.json

Local tighten-the-baseline workflow:

::

    pytest tests/build/ tests/scripts/ --cov=tools/build --cov=scripts \\
        --cov-report=json:/tmp/coverage.json
    python3 scripts/audit_coverage_budget.py --print-baseline > .new-baseline.json
    diff data/baselines/coverage-v9.1.0.json .new-baseline.json

Exit codes
----------

* ``0`` — every tier-1 / tier-2 file is at or above its baseline.
* ``1`` — at least one file regressed beyond tolerance, or a new
  tier-1 / tier-2 file came in below its floor.
* ``2`` — usage / I/O error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# P6 (scripts taxonomy, 2026-05-09) relocated this audit from
# scripts/audit_coverage_budget.py to src/splunk_uc/audits/coverage_budget.py.
# parents[3] resolves: coverage_budget.py -> audits/ -> splunk_uc/ ->
# src/ -> repo root. The legacy `parent.parent` chain assumed a
# one-level depth and is now wrong by three.
REPO_ROOT = Path(__file__).resolve().parents[3]

# Tier 1: the build pipeline core. Coverage targets here are the
# strictest because the build is the production hot path.
TIER_1_INCLUDES = (re.compile(r"^tools/build/.*\.py$"),)

# Files inside tier-1 paths that we deliberately exclude. Generated
# files, one-shot generators, and submodule init helpers all sit here.
TIER_1_EXCLUDES = (
    re.compile(r"^tools/build/migrate_.*\.py$"),
    re.compile(r"^tools/build/generate_.*\.py$"),
)

# Tier 2: the auditing + content-validation CLIs that run in
# ``audits-content`` and ``audits-build``. Anything matching
# ``scripts/audit_*.py`` plus the explicit additions below.
TIER_2_INCLUDES = (
    re.compile(r"^scripts/audit_.*\.py$"),
    re.compile(r"^scripts/equipment_lib\.py$"),
    re.compile(r"^scripts/generate_recommender_app\.py$"),
    re.compile(r"^scripts/build_es\.py$"),
    re.compile(r"^scripts/build_ta\.py$"),
)

# Tier 3 (everything else under scripts/) is documented exempt.
# These are listed for transparency in the baseline JSON; they're
# not used as a gate.
TIER_3_DOCUMENTED_EXEMPT = (
    re.compile(r"^scripts/uplift_.*\.py$"),
    re.compile(r"^scripts/migrate_.*\.py$"),
    re.compile(r"^scripts/_.*\.py$"),
    re.compile(r"^scripts/backfill_.*\.py$"),
    re.compile(r"^scripts/enrich_.*\.py$"),
    re.compile(r"^scripts/generate_.*\.py$"),  # most are catalogue generators
    re.compile(r"^scripts/ingest/.*\.py$"),
    re.compile(r"^scripts/ingest_.*\.py$"),
)


def _classify(path: str) -> str:
    """Return ``'tier1'``, ``'tier2'``, or ``'tier3'``.

    Order matters: tier-1 wins, then tier-2, then everything else.
    Excludes are evaluated within tier-1.
    """
    if any(p.match(path) for p in TIER_1_INCLUDES) and not any(
        e.match(path) for e in TIER_1_EXCLUDES
    ):
        return "tier1"
    if any(p.match(path) for p in TIER_2_INCLUDES):
        return "tier2"
    return "tier3"


def _short_record(info: dict[str, Any]) -> dict[str, Any]:
    """Pull just the fields we ratchet on out of a coverage.py file record."""
    summary = info["summary"]
    return {
        "covered_lines": summary["covered_lines"],
        "num_statements": summary["num_statements"],
        "percent_covered": round(summary["percent_covered"], 2),
        "missing_lines": summary["missing_lines"],
    }


def _load_coverage_report(report_path: Path) -> dict[str, Any]:
    """Load a coverage.py JSON report and return its ``files`` mapping.

    ``coverage.py`` emits paths relative to the cwd at run-time; we
    re-key them to be repo-root relative + posix-style for JSON
    portability and stable diffs.
    """
    if not report_path.is_file():
        print(
            f"::error::coverage report not found at {report_path}. "
            f"Run pytest with --cov-report=json:{report_path} first.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    files = raw.get("files", {})
    normalised: dict[str, Any] = {}
    for fn, info in files.items():
        # coverage.py paths are sometimes absolute, sometimes relative.
        # Normalise to repo-root-relative posix.
        p = Path(fn)
        try:
            rel = p.resolve().relative_to(REPO_ROOT)
            key = rel.as_posix()
        except ValueError:
            key = p.as_posix()
        normalised[key] = info
    return {"files": normalised, "totals": raw.get("totals", {})}


def _git_head() -> str:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
        ).strip()
        return sha
    except Exception:
        return "unknown"


def _read_version() -> str:
    version_file = REPO_ROOT / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def build_baseline(report_path: Path) -> dict[str, Any]:
    """Construct the baseline JSON object from a coverage.py report.

    Tier-1 / tier-2 files are inlined with their per-file coverage
    record; tier-3 files are listed in ``tier_3_exempt`` for
    transparency but not measured.
    """
    cov = _load_coverage_report(report_path)
    tier1: dict[str, dict[str, Any]] = {}
    tier2: dict[str, dict[str, Any]] = {}
    tier3_seen: set[str] = set()
    for fn, info in cov["files"].items():
        match _classify(fn):
            case "tier1":
                tier1[fn] = _short_record(info)
            case "tier2":
                tier2[fn] = _short_record(info)
            case "tier3":
                tier3_seen.add(fn)

    totals = cov["totals"]
    return {
        "$schema": "../../schemas/coverage-baseline.schema.json",
        "version": _read_version(),
        "captured_at": _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": _git_head(),
        "totals": {
            "covered_lines": totals.get("covered_lines", 0),
            "num_statements": totals.get("num_statements", 0),
            "percent_covered": round(totals.get("percent_covered", 0.0), 2),
            "missing_lines": totals.get("missing_lines", 0),
        },
        "tier_1_modules": dict(sorted(tier1.items())),
        "tier_2_modules": dict(sorted(tier2.items())),
        "tier_3_exempt": sorted(tier3_seen),
    }


def check(
    baseline_path: Path,
    report_path: Path,
    *,
    tolerance: float,
    tier1_floor: float,
    tier2_floor: float,
) -> int:
    """Return non-zero exit code on regressions.

    Compares the fresh report against the committed baseline:
    every tier-1 / tier-2 file in the baseline must still be covered
    at ``baseline - tolerance`` or better; every tier-1 / tier-2 file
    introduced *since* the baseline must clear its tier floor.
    """
    if not baseline_path.is_file():
        print(
            f"::error::baseline not found at {baseline_path}. "
            f"Generate one with --print-baseline first.",
            file=sys.stderr,
        )
        return 2
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    cov = _load_coverage_report(report_path)

    failures: list[str] = []
    warnings: list[str] = []

    for tier_key, floor, label in (
        ("tier_1_modules", tier1_floor, "tier-1"),
        ("tier_2_modules", tier2_floor, "tier-2"),
    ):
        bmap: dict[str, dict[str, Any]] = baseline.get(tier_key, {})

        for fn, baseline_record in bmap.items():
            current = cov["files"].get(fn)
            if current is None:
                # File was deleted. Record a warning but don't fail —
                # deleting a tier-1 file is allowed if the rest of the
                # baseline absorbs the loss.
                warnings.append(f"  - {label} file {fn!r} disappeared since the baseline.")
                continue
            new_pct = current["summary"]["percent_covered"]
            old_pct = baseline_record["percent_covered"]
            delta = new_pct - old_pct
            if delta < -tolerance:
                failures.append(
                    f"  ✗ {label}  {fn:60}  {old_pct:5.1f}% → {new_pct:5.1f}%  (Δ {delta:+5.2f}pp, tolerance {tolerance:.2f}pp)"
                )

        # Newly-introduced tier-N files
        for fn, info in cov["files"].items():
            tier = _classify(fn)
            if tier != tier_key.replace("_modules", "").replace("_", ""):
                continue
            if fn in bmap:
                continue
            new_pct = info["summary"]["percent_covered"]
            if new_pct < floor:
                failures.append(
                    f"  ✗ {label}  {fn:60}  new file at {new_pct:5.1f}% (floor {floor:.1f}%)"
                )

    if warnings:
        print("Coverage budget warnings:")
        for w in warnings:
            print(w)
    if failures:
        print("Coverage budget regressions:")
        for f in failures:
            print(f)
        print()
        print(
            f"::error::{len(failures)} coverage regression(s) detected. "
            f"Add tests or update {baseline_path.name} (with reasoning) to absorb."
        )
        return 1

    print(f"OK: every tier-1 / tier-2 file is within {tolerance:.2f}pp of the baseline.")
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit_coverage_budget.py",
        description=__doc__.split("\n\n", 1)[0] if __doc__ else None,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--baseline",
        type=Path,
        default=REPO_ROOT / "data" / "baselines" / "coverage-v9.1.0.json",
        help="Path to the committed coverage baseline JSON.",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=Path("/tmp/coverage.json"),
        help="Path to a fresh coverage.py JSON report.",
    )
    p.add_argument(
        "--tolerance",
        type=float,
        default=1.0,
        help="Allowed regression in percentage points before failing CI (default: 1.0).",
    )
    p.add_argument(
        "--tier1-floor",
        type=float,
        default=60.0,
        help="Minimum coverage percentage for newly-introduced tier-1 files (default: 60.0).",
    )
    p.add_argument(
        "--tier2-floor",
        type=float,
        default=40.0,
        help="Minimum coverage percentage for newly-introduced tier-2 files (default: 40.0).",
    )
    p.add_argument(
        "--print-baseline",
        action="store_true",
        help="Compute a fresh baseline from --report and print it as JSON to stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if args.print_baseline:
        baseline = build_baseline(args.report)
        json.dump(baseline, sys.stdout, indent=2, sort_keys=False)
        sys.stdout.write("\n")
        return 0
    return check(
        baseline_path=args.baseline,
        report_path=args.report,
        tolerance=args.tolerance,
        tier1_floor=args.tier1_floor,
        tier2_floor=args.tier2_floor,
    )


if __name__ == "__main__":
    raise SystemExit(main())
