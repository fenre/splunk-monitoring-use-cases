#!/usr/bin/env python3
"""audit_sandbox_validation.py - Phase 4.5c sandbox validation gate.

Walks every UC sidecar under ``use-cases/cat-*/uc-*.json`` and verifies
that every ``controlTest.fixtureRef`` reference:

1.  Resolves to a file on disk under ``sample-data/``.
2.  Is valid JSON.
3.  Follows one of the two accepted fixture shapes:
    *  **phase2** (preferred): top-level keys ``uc_id``, ``description``,
       ``events_positive`` (array), ``events_negative`` (array).
       Optional ``$comment``.
    *  **legacy**: top-level keys ``description`` (optional),
       ``positiveCase`` (object with ``events`` array, ``expectedFire``),
       ``negativeCase`` (object with ``events`` array, ``expectedFire``).
4.  Has the correct ``expectedFire`` polarity on each case
    (positive=true, negative=false).

For every UC with a fixture, the script classifies its status as one of:

    - ``populated``  - fixture exists, parses, and has at least one event
      in each case.
    - ``empty``      - fixture exists and parses but both event arrays are
      empty.  Typical for Phase 1.6 placeholders.  Not a hard failure.
    - ``half-empty`` - only one of the two cases has events.  Reported as
      a gap but not a hard failure.
    - ``missing``    - ``fixtureRef`` is cited in the UC sidecar but the
      file does not exist.  Reported as a gap but not a hard failure
      (these are tracked for Phase 5 sign-off; the CI never had them
      before and we do not want to retroactively break 80 UCs).
    - ``malformed``  - fixture exists but fails one of the structural
      checks above.  **Hard failure** - exits 1.
    - ``bad-json``   - fixture exists but does not parse.  **Hard
      failure** - exits 1.

The script also cross-checks ``assurance: full`` UCs: a ``full`` claim
is expected to sit on top of a ``populated`` fixture.  ``full`` claims
on ``missing`` / ``empty`` / ``half-empty`` fixtures are **warnings**
(reported in the output and in ``reports/sandbox-validation.json``) but
do not fail the gate; they are the tracking signal Phase 5.2 (SME
sign-off) consumes.

Output
------

``reports/sandbox-validation.json``: deterministic, sorted, machine-
readable rollup of every UC with a ``fixtureRef`` or with an
``assurance: full`` compliance entry.  The file is generated with
``sort_keys=True`` and a trailing newline so the CI determinism guard
can diff-check it.

Exit codes
----------

    0  All fixtures are either resolvable and well-formed, or cleanly
       identified as placeholders.  Warnings may be present but the
       gate is GREEN.
    1  At least one fixture is malformed or unparseable, or the
       ``reports/`` directory cannot be written.

Usage
-----

    python3 scripts/audit_sandbox_validation.py
    python3 scripts/audit_sandbox_validation.py --check   # diff-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"
SAMPLE_DATA = REPO / "sample-data"
REPORT_PATH = REPO / "reports" / "sandbox-validation.json"

STATUS_MISSING = "missing"
STATUS_BAD_JSON = "bad-json"
STATUS_MALFORMED = "malformed"
STATUS_EMPTY = "empty"
STATUS_HALF_EMPTY = "half-empty"
STATUS_POPULATED = "populated"

HARD_FAIL_STATUSES = {STATUS_BAD_JSON, STATUS_MALFORMED}

FIXTURE_SHAPE_PHASE2 = "phase2"
FIXTURE_SHAPE_LEGACY = "legacy"


def _load_uc_sidecar(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _classify_fixture(
    fixture_path: Path,
) -> tuple[str, str | None, int, int, list[str]]:
    """Inspect ``fixture_path`` and return
    ``(status, shape, pos_events, neg_events, issues)``.

    ``status`` is one of the ``STATUS_*`` constants.  ``shape`` is
    ``"phase2"`` / ``"legacy"`` / ``None``.  ``pos_events`` and
    ``neg_events`` are event counts (0 when unknown).  ``issues`` is a
    list of human-readable notes describing why the fixture failed the
    structural check, when applicable.
    """
    if not fixture_path.is_file():
        return (STATUS_MISSING, None, 0, 0, [])

    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        return (STATUS_BAD_JSON, None, 0, 0, [f"parse error: {err}"])

    if not isinstance(payload, dict):
        return (
            STATUS_MALFORMED,
            None,
            0,
            0,
            [f"top-level JSON is {type(payload).__name__}, expected object"],
        )

    issues: list[str] = []

    if "events_positive" in payload and "events_negative" in payload:
        shape = FIXTURE_SHAPE_PHASE2
        pos = payload.get("events_positive")
        neg = payload.get("events_negative")
        if not isinstance(pos, list):
            issues.append("'events_positive' is not a list")
        if not isinstance(neg, list):
            issues.append("'events_negative' is not a list")
        if issues:
            return (STATUS_MALFORMED, shape, 0, 0, issues)
        pos_events = len(pos)
        neg_events = len(neg)
    elif "positiveCase" in payload and "negativeCase" in payload:
        shape = FIXTURE_SHAPE_LEGACY
        pc = payload.get("positiveCase") or {}
        nc = payload.get("negativeCase") or {}
        if not isinstance(pc, dict) or not isinstance(nc, dict):
            issues.append("'positiveCase'/'negativeCase' must be objects")
            return (STATUS_MALFORMED, shape, 0, 0, issues)
        pos_list = pc.get("events")
        neg_list = nc.get("events")
        if not isinstance(pos_list, list):
            issues.append("'positiveCase.events' is not a list")
        if not isinstance(neg_list, list):
            issues.append("'negativeCase.events' is not a list")
        if pc.get("expectedFire") is not True:
            issues.append(
                f"'positiveCase.expectedFire' must be true (got {pc.get('expectedFire')!r})"
            )
        if nc.get("expectedFire") is not False:
            issues.append(
                f"'negativeCase.expectedFire' must be false (got {nc.get('expectedFire')!r})"
            )
        if issues:
            return (STATUS_MALFORMED, shape, 0, 0, issues)
        pos_events = len(pos_list)
        neg_events = len(neg_list)
    else:
        return (
            STATUS_MALFORMED,
            None,
            0,
            0,
            [
                "fixture does not match either accepted shape "
                "(phase2: events_positive/events_negative OR "
                "legacy: positiveCase/negativeCase)"
            ],
        )

    if pos_events == 0 and neg_events == 0:
        return (STATUS_EMPTY, shape, pos_events, neg_events, [])
    if pos_events == 0 or neg_events == 0:
        return (STATUS_HALF_EMPTY, shape, pos_events, neg_events, [])
    return (STATUS_POPULATED, shape, pos_events, neg_events, [])


def _collect_records() -> tuple[list[dict], dict]:
    """Walk the UC sidecars and return the deterministic records list
    plus an aggregate summary.

    A record is emitted for every UC that either cites a
    ``controlTest.fixtureRef`` OR has at least one ``compliance[]`` entry
    with ``assurance == "full"``.  The latter covers UCs that make a
    ``full`` claim without declaring a fixture, which is itself a
    trackable gap.
    """
    records: list[dict] = []
    summary: dict[str, Any] = {
        "total_ucs_examined": 0,
        "with_fixture_ref": 0,
        "with_full_assurance": 0,
        "statuses": {
            STATUS_MISSING: 0,
            STATUS_BAD_JSON: 0,
            STATUS_MALFORMED: 0,
            STATUS_EMPTY: 0,
            STATUS_HALF_EMPTY: 0,
            STATUS_POPULATED: 0,
            "no-fixture": 0,
        },
        "full_assurance_with_gap": 0,
        "hard_failures": 0,
    }

    for sidecar_path in sorted(USE_CASES.glob("cat-*/uc-*.json")):
        data = _load_uc_sidecar(sidecar_path)
        if data is None:
            # Broken sidecars are caught by audit_compliance_mappings;
            # we silently skip so we don't double-report errors.
            continue

        summary["total_ucs_examined"] += 1

        uc_id = data.get("id") or sidecar_path.stem.removeprefix("uc-")
        control_test = data.get("controlTest") or {}
        fixture_ref = control_test.get("fixtureRef")
        compliance = data.get("compliance") or []
        full_entries = [
            e
            for e in compliance
            if isinstance(e, dict) and e.get("assurance") == "full"
        ]
        has_full = len(full_entries) > 0
        if has_full:
            summary["with_full_assurance"] += 1

        if not fixture_ref:
            if has_full:
                # UC claims 'full' assurance but declares no fixture.
                # Record this so Phase 5.2 SME review can target it.
                records.append(
                    {
                        "uc_id": uc_id,
                        "sidecar": str(sidecar_path.relative_to(REPO)),
                        "fixtureRef": None,
                        "status": "no-fixture",
                        "shape": None,
                        "pos_events": 0,
                        "neg_events": 0,
                        "issues": [],
                        "full_assurance": True,
                        "full_assurance_clauses": sorted(
                            {
                                f"{e.get('regulation', '?')}:{e.get('clause', '?')}"
                                for e in full_entries
                            }
                        ),
                    }
                )
                summary["statuses"]["no-fixture"] += 1
                summary["full_assurance_with_gap"] += 1
            continue

        summary["with_fixture_ref"] += 1
        fixture_path = REPO / fixture_ref
        status, shape, pos, neg, issues = _classify_fixture(fixture_path)
        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
        if status in HARD_FAIL_STATUSES:
            summary["hard_failures"] += 1

        full_gap = has_full and status in {
            STATUS_MISSING,
            STATUS_EMPTY,
            STATUS_HALF_EMPTY,
        }
        if full_gap:
            summary["full_assurance_with_gap"] += 1

        records.append(
            {
                "uc_id": uc_id,
                "sidecar": str(sidecar_path.relative_to(REPO)),
                "fixtureRef": fixture_ref,
                "status": status,
                "shape": shape,
                "pos_events": pos,
                "neg_events": neg,
                "issues": issues,
                "full_assurance": has_full,
                "full_assurance_clauses": sorted(
                    {
                        f"{e.get('regulation', '?')}:{e.get('clause', '?')}"
                        for e in full_entries
                    }
                ),
            }
        )

    records.sort(key=lambda r: (r["uc_id"], r["sidecar"]))
    return records, summary


def _render_report(records: list[dict], summary: dict) -> str:
    """Return the deterministic JSON payload to write to
    ``reports/sandbox-validation.json``.

    The top-level keys are alphabetised; the ``records`` list is sorted
    by ``uc_id`` so diff checking in CI is stable.
    """
    payload = {
        "$comment": (
            "Phase 4.5c sandbox validation report. Generated by "
            "scripts/audit_sandbox_validation.py. Hard failures (malformed "
            "or unparseable fixtures) block CI; missing/empty fixtures are "
            "tracked gaps for Phase 5.2 SME review. See "
            "docs/peer-review-guide.md \u00a73.2 for the assurance contract."
        ),
        "records": records,
        "summary": summary,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _print_human_summary(records: list[dict], summary: dict) -> None:
    print("=== Sandbox validation gate ===")
    print(f"Total UC sidecars examined : {summary['total_ucs_examined']}")
    print(f"UCs with fixtureRef         : {summary['with_fixture_ref']}")
    print(f"UCs with 'full' assurance   : {summary['with_full_assurance']}")
    print()
    print("Fixture status distribution :")
    for status in sorted(summary["statuses"].keys()):
        count = summary["statuses"][status]
        if count:
            print(f"  {status:<14} {count}")
    print()
    print(f"'full' claims on gap fixtures: {summary['full_assurance_with_gap']}")
    print(f"Hard failures (CI blocker)   : {summary['hard_failures']}")
    if summary["hard_failures"]:
        print()
        print("Hard failures:")
        for rec in records:
            if rec["status"] in HARD_FAIL_STATUSES:
                print(
                    f"  {rec['uc_id']:<12} {rec['status']:<10} "
                    f"{rec['fixtureRef']}"
                )
                for issue in rec["issues"]:
                    print(f"    - {issue}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4.5c sandbox validation gate."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the regenerated report to the committed "
        "reports/sandbox-validation.json and exit non-zero on drift. "
        "Used by the CI determinism guard.",
    )
    args = parser.parse_args(argv)

    records, summary = _collect_records()
    payload_str = _render_report(records, summary)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        if not REPORT_PATH.is_file():
            sys.stderr.write(
                f"ERROR: --check requested but {REPORT_PATH} does not exist. "
                "Run without --check first to generate it.\n"
            )
            return 1
        existing = REPORT_PATH.read_text(encoding="utf-8")
        if existing != payload_str:
            sys.stderr.write(
                "ERROR: sandbox-validation.json is out of date. "
                "Run `python3 scripts/audit_sandbox_validation.py` and "
                "commit the updated report.\n"
            )
            return 1
    else:
        REPORT_PATH.write_text(payload_str, encoding="utf-8")

    _print_human_summary(records, summary)
    print()
    if summary["hard_failures"]:
        print("=== SANDBOX GATE: RED ===")
        return 1
    print("=== SANDBOX GATE: GREEN ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
