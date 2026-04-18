#!/usr/bin/env python3
"""audit_perf_a11y.py — Phase 4.5f performance + accessibility audit gate.

Two independent dimensions are enforced in a single CI step because
both speak to "what ships to the end user":

1. **Performance budget.**  The repo ships a static site that is often
   loaded under flaky conference Wi-Fi by auditors, privacy officers
   and regulators on mobile devices.  Runaway file-size regressions
   (a developer accidentally inlines catalog.json into data.js, a
   merge conflict duplicates a script block, someone checks in a huge
   SVG) break that experience silently.  Each critical asset has a
   hard-coded byte budget; any file over budget hard-fails CI.  Budget
   numbers are set with ~25 % headroom against the current footprint
   so routine content growth does not flicker the gate.

2. **Accessibility (axe-core under jsdom).**  The project is marketed
   as the "international gold standard for logging and compliance
   visibility" and is consumed by legal / risk / executive stakeholders
   who are frequently covered by accessibility mandates (Section 508
   in the US, EN 301 549 in the EU, EAA 2025, AODA in Canada).  We
   therefore run axe-core v4 against every user-facing HTML page with
   the WCAG 2.1 A+AA + best-practice ruleset.  Severe violations
   (``impact=critical`` or ``impact=serious``) hard-fail the gate
   unless allowlisted; moderate / minor violations surface as
   warnings; jsdom-incomplete rules (e.g. ``landmark-one-main`` when
   the main landmark is hydrated by client JS) are downgraded to
   informational to keep the signal clean.

The Node runner lives at ``tests/a11y/run-axe.mjs`` — this script is a
thin orchestrator that (a) invokes the runner, (b) layers budget
checks on top, (c) applies the inline allowlist, and (d) emits a
deterministic ``reports/perf-a11y.json`` report that CI can upload
as an artifact.

Output
------

``reports/perf-a11y.json`` is serialised with
``json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\\n"``
— the same canonical form used across the repo so the file diffs
stably and downstream tools (Node drift test, auditor tooling) can
rely on byte-equality.

Exit codes
----------

    0   No hard failures.
    1   At least one budget overrun, serious/critical a11y violation
        that is not allowlisted, or axe-core runner error.  In
        ``--check`` mode, also 1 if the committed report differs from
        the freshly-generated one.

Usage
-----

    python3 scripts/audit_perf_a11y.py
    python3 scripts/audit_perf_a11y.py --check   # drift-check only
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO / "reports" / "perf-a11y.json"
RUN_AXE_SCRIPT = REPO / "tests" / "a11y" / "run-axe.mjs"

# ---------------------------------------------------------------------------
# Performance budgets
# ---------------------------------------------------------------------------
#
# Each entry is ``(relative path, budget_bytes, tier, note)`` where tier is
# one of:
#   * "critical-path"  - user-facing HTML / JS.  Strict budget.
#   * "generated-data" - build artefacts (catalog, data, llms).  Looser
#                        budget because content growth is expected.
#
# Budgets are absolute byte counts (not KiB shorthand) so the source
# of truth is unambiguous; every change to a budget is reviewed as a
# single-number diff and explained in the accompanying note.
#
# How budgets are set:
#   current_size  * 1.25  rounded up to a convenient byte boundary.
#   This gives ~25 % headroom for routine growth before the gate
#   requires review.  Tighten budgets only when you have an active
#   perf-regression story; loosen them only with a recorded business
#   reason in the CHANGELOG so the size drift is auditable.
# ---------------------------------------------------------------------------
PerfBudget = dict[str, Any]

_PERF_BUDGETS: list[PerfBudget] = [
    {
        "file": "index.html",
        "budget_bytes": 440_320,  # ~430 KiB
        "tier": "critical-path",
        "note": (
            "Main catalog landing page; inlines all CSS/JS for offline "
            "auditor mode.  Budget sized to tolerate the release-notes "
            "popup + non-technical visualisations growing 25 %."
        ),
    },
    {
        "file": "scorecard.html",
        "budget_bytes": 65_536,  # 64 KiB
        "tier": "critical-path",
        "note": (
            "Auditor-facing compliance scorecard.  Budget deliberately "
            "tight — the page is a dashboard and must load fast under "
            "conference Wi-Fi."
        ),
    },
    {
        "file": "custom-text.js",
        "budget_bytes": 4_096,  # 4 KiB
        "tier": "critical-path",
        "note": (
            "Per-deployment text overrides (watermarks, copyright). "
            "Should never be large; budget catches accidental inlining."
        ),
    },
    {
        "file": "provenance.js",
        "budget_bytes": 131_072,  # 128 KiB
        "tier": "critical-path",
        "note": (
            "Provenance overlay shown to auditors.  Budget sized to "
            "absorb modest catalogue growth; exceeding it suggests "
            "provenance metadata is being duplicated across UCs."
        ),
    },
    {
        "file": "llms.txt",
        "budget_bytes": 20_480,  # 20 KiB
        "tier": "critical-path",
        "note": (
            "llms.txt is the compact AI-agent discovery manifest. "
            "Per the llms.txt spec this is intended to fit in a model's "
            "short-term context window, so the budget is deliberately "
            "small to catch accidental promotion from llms-full.txt."
        ),
    },
    {
        "file": "data.js",
        "budget_bytes": 52_428_800,  # 50 MiB
        "tier": "generated-data",
        "note": (
            "Full catalogue payload loaded by index.html.  Budget "
            "sized for 800+ UCs; tightening requires renegotiating "
            "the build.py canonical serialiser."
        ),
    },
    {
        "file": "catalog.json",
        "budget_bytes": 58_720_256,  # 56 MiB
        "tier": "generated-data",
        "note": (
            "Raw JSON twin of data.js for AI agents / scripted "
            "consumers.  Slightly larger budget than data.js because "
            "the JSON form is unminified."
        ),
    },
    {
        "file": "llms-full.txt",
        "budget_bytes": 655_360,  # 640 KiB
        "tier": "generated-data",
        "note": (
            "Long-form AI-agent manifest (per llms.txt spec).  Budget "
            "sized for routine UC content growth."
        ),
    },
]

# ---------------------------------------------------------------------------
# A11Y configuration
# ---------------------------------------------------------------------------
#
# Pages audited by axe-core.  Order matters: the report preserves this
# order so auditors scanning the report see the auditor-facing
# scorecard first.
_A11Y_PAGES: list[str] = [
    "scorecard.html",
    "index.html",
]

# axe-core impact levels considered hard failures.  "minor" and
# "moderate" are surfaced as warnings (still reported and still
# auditable, but they do not block merges).  axe docs:
# https://dequeuniversity.com/rules/axe/  (impact column).
_HARD_FAIL_IMPACTS: set[str] = {"critical", "serious"}
_WARNING_IMPACTS: set[str] = {"moderate", "minor"}

# Allowlist of (file, rule_id) tuples that are explicitly tolerated.
# Adding an entry here is a conscious decision that should be recorded
# in the CHANGELOG and reviewed by a peer reviewer per
# ``docs/peer-review-guide.md``.  Keep this list short; every entry
# represents accessibility debt.
#
# Each entry: {
#   "file": "path.html",
#   "rule_id": "aria-dialog-name",
#   "reason": "explanation",
#   "approver": "team/person",
#   "added": "YYYY-MM-DD",
#   "review_by": "YYYY-MM-DD",
# }
_A11Y_ALLOWLIST: list[dict[str, str]] = []


# ---------------------------------------------------------------------------
# Budget evaluation
# ---------------------------------------------------------------------------


def _evaluate_budgets(budgets: list[PerfBudget]) -> tuple[list[dict[str, Any]], int]:
    """Return ``(records, hard_failures)``.

    Every field on the record is either a string or an integer — we do
    not emit floating-point values.  The report is consumed cross-
    language (Node drift test under ``tests/a11y/perfa11y.test.mjs``)
    and Python's ``json.dumps(55.0)`` produces ``"55.0"`` while
    JavaScript's ``JSON.stringify(55.0)`` produces ``"55"`` — floats
    that happen to have a zero fractional part therefore break the
    byte-equality contract.  Consumers that need percentage headroom
    derive it on the fly from ``headroom_bytes / budget_bytes``.  The
    human summary computes it for display but never writes it into
    the canonical JSON.
    """
    records: list[dict[str, Any]] = []
    hard_failures = 0
    for spec in budgets:
        rel = spec["file"]
        budget = int(spec["budget_bytes"])
        abs_path = REPO / rel
        if not abs_path.is_file():
            records.append(
                {
                    "actual_bytes": None,
                    "budget_bytes": budget,
                    "file": rel,
                    "headroom_bytes": None,
                    "note": spec.get("note", ""),
                    "status": "missing",
                    "tier": spec.get("tier", "critical-path"),
                }
            )
            hard_failures += 1
            continue

        actual = abs_path.stat().st_size
        headroom = budget - actual
        status = "ok" if actual <= budget else "over-budget"
        if status == "over-budget":
            hard_failures += 1
        records.append(
            {
                "actual_bytes": actual,
                "budget_bytes": budget,
                "file": rel,
                "headroom_bytes": headroom,
                "note": spec.get("note", ""),
                "status": status,
                "tier": spec.get("tier", "critical-path"),
            }
        )

    records.sort(key=lambda r: (r["tier"], r["file"]))
    return records, hard_failures


# ---------------------------------------------------------------------------
# A11y evaluation
# ---------------------------------------------------------------------------


def _run_axe(pages: list[str]) -> dict[str, Any]:
    """Invoke ``tests/a11y/run-axe.mjs`` as a subprocess.

    Returns the parsed JSON payload.  Raises ``RuntimeError`` if the
    subprocess fails or emits non-JSON output, so the caller can
    decide how to surface the failure.  We deliberately do not swallow
    these errors: a broken axe runner is itself a CI-blocking signal.
    """
    if not RUN_AXE_SCRIPT.is_file():
        raise RuntimeError(
            f"axe runner missing at {RUN_AXE_SCRIPT.relative_to(REPO)}"
        )
    node = shutil.which("node")
    if node is None:
        raise RuntimeError(
            "`node` binary not found on PATH.  Install Node.js 20+ "
            "and run `npm ci` before invoking this audit."
        )
    node_modules = REPO / "node_modules"
    if not (node_modules / "axe-core").is_dir():
        raise RuntimeError(
            "node_modules/axe-core is missing.  Run `npm ci` in the "
            "repo root to install axe-core and jsdom before invoking "
            "this audit."
        )
    if not (node_modules / "jsdom").is_dir():
        raise RuntimeError(
            "node_modules/jsdom is missing.  Run `npm ci` in the repo "
            "root to install axe-core and jsdom before invoking this "
            "audit."
        )

    cmd = [node, str(RUN_AXE_SCRIPT), *pages]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"axe runner exited with code {proc.returncode}.\n"
            f"stdout: {proc.stdout[:500]}\n"
            f"stderr: {proc.stderr[:500]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as err:
        raise RuntimeError(
            "axe runner produced non-JSON output:\n"
            f"{proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
        ) from err


def _is_allowlisted(file: str, rule_id: str) -> bool:
    for entry in _A11Y_ALLOWLIST:
        if entry.get("file") == file and entry.get("rule_id") == rule_id:
            return True
    return False


def _evaluate_a11y(
    axe_payload: dict[str, Any],
) -> tuple[dict[str, Any], int, int, int]:
    """Evaluate axe-runner output against impact thresholds + allowlist.

    Returns ``(a11y_block, hard_failures, warnings, total_violations)``.
    """
    results = axe_payload.get("results") or []
    annotated_results: list[dict[str, Any]] = []
    hard_failures = 0
    warnings = 0
    total_violations = 0
    allowlist_hits: list[dict[str, str]] = []

    for result in results:
        file = result.get("file", "?")
        if result.get("status") != "ok":
            # Runner error on this file is itself a hard failure.
            annotated_results.append(
                {
                    "error": result.get("error"),
                    "file": file,
                    "hard_failure_count": 1,
                    "incomplete": result.get("incomplete") or [],
                    "status": "error",
                    "summary": result.get("summary") or {
                        "incomplete": 0,
                        "inapplicable": 0,
                        "passes": 0,
                        "violations": 0,
                    },
                    "violations": result.get("violations") or [],
                    "warning_count": 0,
                }
            )
            hard_failures += 1
            continue

        violations = result.get("violations") or []
        total_violations += len(violations)
        file_hard = 0
        file_warn = 0
        annotated_violations: list[dict[str, Any]] = []
        for v in violations:
            impact = (v.get("impact") or "unknown").lower()
            allowlisted = _is_allowlisted(file, v.get("id") or "")
            disposition = "hard-fail"
            if allowlisted:
                disposition = "allowlisted"
            elif impact in _HARD_FAIL_IMPACTS:
                disposition = "hard-fail"
            elif impact in _WARNING_IMPACTS:
                disposition = "warning"
            else:
                # Unknown impact — treat conservatively as a warning
                # so it surfaces in the report without blocking merges.
                disposition = "warning"

            if disposition == "hard-fail":
                file_hard += 1
            elif disposition == "warning":
                file_warn += 1
            elif disposition == "allowlisted":
                allowlist_hits.append(
                    {
                        "file": file,
                        "rule_id": v.get("id") or "",
                    }
                )

            annotated_violations.append({**v, "disposition": disposition})

        incomplete = result.get("incomplete") or []
        annotated_results.append(
            {
                "error": None,
                "file": file,
                "hard_failure_count": file_hard,
                "incomplete": incomplete,
                "status": "ok",
                "summary": result.get("summary") or {
                    "incomplete": len(incomplete),
                    "inapplicable": 0,
                    "passes": 0,
                    "violations": len(violations),
                },
                "violations": annotated_violations,
                "warning_count": file_warn,
            }
        )
        hard_failures += file_hard
        warnings += file_warn

    allowlist_snapshot = sorted(
        (
            {
                "added": entry.get("added", ""),
                "approver": entry.get("approver", ""),
                "file": entry.get("file", ""),
                "reason": entry.get("reason", ""),
                "review_by": entry.get("review_by", ""),
                "rule_id": entry.get("rule_id", ""),
            }
            for entry in _A11Y_ALLOWLIST
        ),
        key=lambda e: (e["file"], e["rule_id"]),
    )

    a11y_block = {
        "allowlist": allowlist_snapshot,
        "axe_version": axe_payload.get("axe_version", "unknown"),
        "config": axe_payload.get("config") or {},
        "jsdom_version": axe_payload.get("jsdom_version", "unknown"),
        "pages_audited": [r["file"] for r in annotated_results],
        "results": annotated_results,
        "summary": {
            "allowlist_hits": len(allowlist_hits),
            "hard_failures": hard_failures,
            "pages_with_errors": sum(
                1 for r in annotated_results if r["status"] == "error"
            ),
            "total_violations": total_violations,
            "warnings": warnings,
        },
    }
    return a11y_block, hard_failures, warnings, total_violations


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def _canonical_serialise(payload: Any) -> str:
    """Match ``scripts/generate_api_surface.py._write_json`` exactly."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _render_report(
    perf_records: list[dict[str, Any]],
    perf_hard_failures: int,
    a11y_block: dict[str, Any],
    a11y_hard_failures: int,
    a11y_warnings: int,
    axe_runner_error: str | None,
) -> str:
    payload = {
        "$comment": (
            "Phase 4.5f perf + a11y report.  Generated by "
            "scripts/audit_perf_a11y.py.  The perf block enforces "
            "byte budgets on critical-path assets; the a11y block is "
            "axe-core v4 run under jsdom against the WCAG 2.1 A+AA + "
            "best-practice tag set, with color-contrast and other "
            "layout-dependent rules disabled (see tests/a11y/run-axe.mjs). "
            "Serious / critical a11y violations hard-fail CI; moderate / "
            "minor surface as warnings; incomplete results are "
            "informational (jsdom limitation)."
        ),
        "a11y": a11y_block,
        "axe_runner_error": axe_runner_error,
        "perf": {
            "budgets": perf_records,
            "summary": {
                "generated_data_budgeted": sum(
                    1 for r in perf_records if r["tier"] == "generated-data"
                ),
                "critical_path_budgeted": sum(
                    1 for r in perf_records if r["tier"] == "critical-path"
                ),
                "hard_failures": perf_hard_failures,
                "missing_count": sum(
                    1 for r in perf_records if r["status"] == "missing"
                ),
                "over_budget_count": sum(
                    1 for r in perf_records if r["status"] == "over-budget"
                ),
                "total_files": len(perf_records),
            },
        },
        "summary": {
            "a11y_hard_failures": a11y_hard_failures,
            "a11y_warnings": a11y_warnings,
            "hard_failures": perf_hard_failures
            + a11y_hard_failures
            + (1 if axe_runner_error else 0),
            "perf_hard_failures": perf_hard_failures,
            "runner_error": bool(axe_runner_error),
        },
    }
    return _canonical_serialise(payload)


def _print_human_summary(
    perf_records: list[dict[str, Any]],
    perf_hard_failures: int,
    a11y_block: dict[str, Any],
    a11y_hard_failures: int,
    a11y_warnings: int,
    axe_runner_error: str | None,
) -> None:
    print("=== Perf + a11y gate ===")
    print()
    print("-- Performance budgets --")
    for rec in perf_records:
        if rec["status"] == "missing":
            status_str = "MISSING"
        elif rec["status"] == "over-budget":
            status_str = "OVER"
        else:
            status_str = "ok"
        if rec["actual_bytes"] is None:
            actual_s = "         -"
            headroom_s = ""
        else:
            actual_s = f"{rec['actual_bytes']:>10}"
            headroom_pct = (
                rec["headroom_bytes"] / rec["budget_bytes"] * 100.0
                if rec["budget_bytes"]
                else 0.0
            )
            headroom_s = f" ({headroom_pct:.2f}% headroom)"
        print(
            f"  [{status_str:<7}] {rec['file']:<22} "
            f"{actual_s} / {rec['budget_bytes']:>10} bytes{headroom_s}"
        )
    print(f"  perf hard failures: {perf_hard_failures}")
    print()

    if axe_runner_error:
        print("-- A11Y --")
        print(f"  RUNNER ERROR: {axe_runner_error}")
        print()
        print("=== PERF+A11Y GATE: RED ===")
        return

    print("-- Accessibility (axe-core) --")
    summary = a11y_block.get("summary", {})
    print(f"  axe-core version : {a11y_block.get('axe_version')}")
    print(f"  jsdom version    : {a11y_block.get('jsdom_version')}")
    print(f"  pages audited    : {len(a11y_block.get('pages_audited', []))}")
    print(f"  total violations : {summary.get('total_violations', 0)}")
    print(f"  hard failures    : {summary.get('hard_failures', 0)}")
    print(f"  warnings         : {summary.get('warnings', 0)}")
    print(f"  allowlist hits   : {summary.get('allowlist_hits', 0)}")
    print(f"  pages w/ errors  : {summary.get('pages_with_errors', 0)}")

    for result in a11y_block.get("results", []):
        file = result.get("file")
        status = result.get("status")
        summary = result.get("summary", {})
        violations = result.get("violations", [])
        incomplete = result.get("incomplete", [])
        print()
        print(
            f"  {file} "
            f"[passes={summary.get('passes', 0)}, "
            f"violations={summary.get('violations', 0)}, "
            f"incomplete={summary.get('incomplete', 0)}, "
            f"inapplicable={summary.get('inapplicable', 0)}]"
        )
        if status != "ok":
            print(f"    RUNNER ERROR on this file: {result.get('error')}")
            continue
        for v in violations:
            print(
                f"    [{v.get('disposition', '?'):<11}] "
                f"{v.get('impact', '?'):<8} {v.get('id')}"
                f" ({v.get('nodeCount')} nodes): {v.get('help', '')[:80]}"
            )
        for v in incomplete[:5]:
            print(
                f"    [incomplete] "
                f"{v.get('impact', '?'):<8} {v.get('id')}"
                f" ({v.get('nodeCount')} nodes): {v.get('help', '')[:80]}"
            )
        if len(incomplete) > 5:
            print(f"    [incomplete] ... {len(incomplete) - 5} more")

    print()
    if perf_hard_failures + a11y_hard_failures:
        print("=== PERF+A11Y GATE: RED ===")
    else:
        print("=== PERF+A11Y GATE: GREEN ===")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4.5f performance + accessibility gate."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate the report in memory and diff against the "
            "committed reports/perf-a11y.json; exit non-zero on drift."
        ),
    )
    args = parser.parse_args(argv)

    perf_records, perf_hard_failures = _evaluate_budgets(_PERF_BUDGETS)

    axe_runner_error: str | None = None
    try:
        axe_payload = _run_axe(_A11Y_PAGES)
    except RuntimeError as err:
        axe_runner_error = str(err)
        axe_payload = {
            "axe_version": "unknown",
            "config": {"disabled_rules": [], "run_only": {}},
            "jsdom_version": "unknown",
            "results": [],
        }
        sys.stderr.write(f"ERROR: {err}\n")

    a11y_block, a11y_hard_failures, a11y_warnings, _ = _evaluate_a11y(axe_payload)

    payload_str = _render_report(
        perf_records,
        perf_hard_failures,
        a11y_block,
        a11y_hard_failures,
        a11y_warnings,
        axe_runner_error,
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        if not REPORT_PATH.is_file():
            sys.stderr.write(
                f"ERROR: --check requested but {REPORT_PATH.relative_to(REPO)} "
                "does not exist. Run without --check first to generate it.\n"
            )
            return 1
        existing = REPORT_PATH.read_text(encoding="utf-8")
        if existing != payload_str:
            sys.stderr.write(
                "ERROR: perf-a11y.json is out of date. "
                "Run `python3 scripts/audit_perf_a11y.py` and commit "
                "the updated report.\n"
            )
            return 1
    else:
        REPORT_PATH.write_text(payload_str, encoding="utf-8")

    _print_human_summary(
        perf_records,
        perf_hard_failures,
        a11y_block,
        a11y_hard_failures,
        a11y_warnings,
        axe_runner_error,
    )

    total_hard_failures = (
        perf_hard_failures
        + a11y_hard_failures
        + (1 if axe_runner_error else 0)
    )
    return 1 if total_hard_failures else 0


if __name__ == "__main__":
    sys.exit(main())
