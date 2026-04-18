#!/usr/bin/env python3
"""simulate_controltest.py - Phase 4.5d ATT&CK simulation gate.

Walks every UC sidecar under ``use-cases/cat-*/uc-*.json``, inspects each
``controlTest`` block, and produces a deterministic, auditor-readable
simulation report at ``reports/attack-simulation.json``.

Because we cannot run real Splunk SPL in CI (there is no indexer, and
shipping a Splunk Cloud tenant just for the test would leak secrets and
create flakiness), this script is **not** a SPL runtime.  It is a
**structural + semantic simulator** that answers three questions per
UC:

1. **ATT&CK technique integrity.**  If the UC references an ATT&CK
   technique (either in ``controlTest.attackTechnique`` or in the
   top-level ``mitreAttack[]`` list), does that technique ID:

      a) match the canonical MITRE grammar ``T####`` or
         ``T####.###``; and
      b) exist in the committed MITRE ATT&CK crosswalks at
         ``data/crosswalks/attack/mitre-attack-*.normalised.json``?

   Both are **hard failures** if violated — we will not ship a clause
   claiming MITRE coverage that cannot be traced to MITRE's own
   dataset.

2. **Fixture polarity coherence.**  If the UC cites a
   ``controlTest.fixtureRef`` and the fixture is populated, do the
   events actually match the scenario's intent?  Specifically:

      * The positive case must contain at least one event; the
        ``expectedFire`` flag (if present on legacy fixtures) must be
        ``true``.
      * The negative case must contain at least one event; the
        ``expectedFire`` flag (if present on legacy fixtures) must be
        ``false``.

   Polarity inversion is a **hard failure**; empty / half-empty
   fixtures are tracked gaps (handled by
   ``audit_sandbox_validation.py``) and are not re-reported here to
   avoid double-failing the CI on the same root cause.

3. **SPL/fixture coherence heuristic.**  For populated fixtures, we
   extract a lightweight set of ``index=*`` / ``source=*`` /
   ``sourcetype=*`` literals from ``uc.spl`` and check whether the
   positive-case events carry fields that reference at least one of
   those literal values.  This is a **warning**, never a hard failure:
   it is a coherence smoke test that catches copy-paste errors where
   the fixture was authored for a different UC.

The report is written with ``sort_keys=True`` + trailing newline so
the CI determinism guard can diff-check it.

Exit codes
----------

    0  No hard failures.  Warnings + tracked gaps may be present.
    1  At least one hard failure (bad ATT&CK technique ID, unknown
       technique, polarity inversion, or IO error writing the report).

Usage
-----

    python3 scripts/simulate_controltest.py
    python3 scripts/simulate_controltest.py --check   # drift-check only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
USE_CASES = REPO / "use-cases"
REPORT_PATH = REPO / "reports" / "attack-simulation.json"
CROSSWALK_DIR = REPO / "data" / "crosswalks" / "attack"
CROSSWALK_FILES = (
    "mitre-attack-enterprise.normalised.json",
    "mitre-attack-ics.normalised.json",
    "mitre-attack-mobile.normalised.json",
)

# Canonical MITRE technique ID grammar.  Anchored to the whole string
# so ``T1234xyz`` and ``T1234.000a`` fail; leading/trailing whitespace
# is rejected (caller must strip).
ATTACK_ID_RE = re.compile(r"^T\d{4}(?:\.\d{3})?$")

# Lightweight SPL literal extractor.  We deliberately keep this narrow:
# matches ``index=foo``, ``source=foo``, ``sourcetype=foo`` (with or
# without quoting, with wildcards).  It is NOT an SPL parser; it just
# surfaces the most common coherence-test hooks.
SPL_LITERAL_RE = re.compile(
    r"""(?xi)
    \b(?P<field>index|source|sourcetype)\s*=\s*
    (?P<value>
        "(?:[^"\\]|\\.)*"     # double-quoted
        |'(?:[^'\\]|\\.)*'    # single-quoted
        |[^\s|"')\]]+          # bare token (stop at SPL punctuation)
    )
    """
)

STATUS_SIMULATED = "simulated"
STATUS_PENDING = "pending_fixture"
STATUS_NO_FIXTURE = "no_fixture_declared"
STATUS_POLARITY_FAIL = "polarity_mismatch"
STATUS_HEURISTIC_MISMATCH = "spl_fixture_mismatch"

HARD_FAIL_STATUSES = {STATUS_POLARITY_FAIL}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_known_techniques() -> set[str]:
    """Return the union of MITRE ATT&CK technique IDs across the
    Enterprise, ICS, and Mobile crosswalks.

    Missing crosswalk files trigger a hard failure: without the
    dataset we cannot validate technique IDs, and we refuse to emit a
    green report in that condition.
    """
    known: set[str] = set()
    for name in CROSSWALK_FILES:
        path = CROSSWALK_DIR / name
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing MITRE ATT&CK crosswalk: {path}. "
                f"Run scripts/ingest_mitre_attack.py to regenerate."
            )
        payload = _load_json(path)
        for tech in payload.get("techniques", []):
            attack_id = tech.get("attack_id")
            if isinstance(attack_id, str) and ATTACK_ID_RE.match(attack_id):
                known.add(attack_id)
    if not known:
        raise RuntimeError(
            "MITRE ATT&CK crosswalks loaded but 0 techniques found; "
            "dataset is corrupt."
        )
    return known


# ---------------------------------------------------------------------------
# Per-UC analysis
# ---------------------------------------------------------------------------


def _collect_uc_technique_refs(uc: dict) -> list[str]:
    """Return the list of ATT&CK technique IDs referenced by a UC,
    deduplicated and sorted, drawn from ``controlTest.attackTechnique``
    (str or list) and top-level ``mitreAttack`` (list).

    Non-string entries are silently dropped; they are caught elsewhere
    by ``audit_uc_structure`` / ``audit_compliance_mappings``.
    """
    ids: set[str] = set()

    ct = uc.get("controlTest") or {}
    at = ct.get("attackTechnique")
    if isinstance(at, str):
        ids.add(at.strip())
    elif isinstance(at, list):
        for item in at:
            if isinstance(item, str):
                ids.add(item.strip())

    mitre = uc.get("mitreAttack") or []
    if isinstance(mitre, list):
        for item in mitre:
            if isinstance(item, str):
                ids.add(item.strip())

    return sorted(i for i in ids if i)


def _validate_technique_ids(
    refs: list[str], known: set[str]
) -> tuple[list[str], list[str]]:
    """Return ``(bad_format, unknown)`` buckets for the UC's ATT&CK
    references.  ``bad_format`` entries fail the regex; ``unknown``
    entries pass the regex but are absent from the MITRE crosswalk.
    """
    bad_format: list[str] = []
    unknown: list[str] = []
    for ref in refs:
        if not ATTACK_ID_RE.match(ref):
            bad_format.append(ref)
            continue
        if ref not in known:
            unknown.append(ref)
    return bad_format, unknown


def _extract_spl_literals(spl: str) -> dict[str, set[str]]:
    """Return a mapping ``{field -> {literal_value, ...}}`` extracted
    from the SPL string.  Values are stripped of surrounding quotes
    and wildcards are preserved verbatim (so ``sourcetype=cisco:*``
    yields ``cisco:*``).
    """
    out: dict[str, set[str]] = {"index": set(), "source": set(), "sourcetype": set()}
    if not isinstance(spl, str):
        return out
    for m in SPL_LITERAL_RE.finditer(spl):
        field = m.group("field").lower()
        value = m.group("value")
        if value.startswith(('"', "'")):
            value = value[1:-1]
        out.setdefault(field, set()).add(value)
    return out


def _fixture_events(fixture: dict) -> tuple[list[dict], list[dict], str | None]:
    """Return ``(positive_events, negative_events, shape)``.

    ``shape`` is one of ``"phase2"`` / ``"legacy"`` / ``None`` (when
    the fixture does not match either accepted layout; that case is
    already reported by the sandbox validator and we return empty
    event lists here).
    """
    if "events_positive" in fixture or "events_negative" in fixture:
        pos = fixture.get("events_positive") or []
        neg = fixture.get("events_negative") or []
        pos = [e for e in pos if isinstance(e, dict)]
        neg = [e for e in neg if isinstance(e, dict)]
        return pos, neg, "phase2"
    if "positiveCase" in fixture or "negativeCase" in fixture:
        pc = fixture.get("positiveCase") or {}
        nc = fixture.get("negativeCase") or {}
        pos = pc.get("events") or [] if isinstance(pc, dict) else []
        neg = nc.get("events") or [] if isinstance(nc, dict) else []
        pos = [e for e in pos if isinstance(e, dict)]
        neg = [e for e in neg if isinstance(e, dict)]
        return pos, neg, "legacy"
    return [], [], None


def _check_polarity(fixture: dict, shape: str | None) -> list[str]:
    """Return a list of human-readable issues if the fixture's
    ``expectedFire`` flags contradict the positive/negative labels.
    Only applies to the legacy shape; phase2 fixtures encode intent
    structurally (the list name *is* the polarity) so no inversion is
    possible.
    """
    if shape != "legacy":
        return []
    issues: list[str] = []
    pc = fixture.get("positiveCase") or {}
    nc = fixture.get("negativeCase") or {}
    if isinstance(pc, dict) and pc.get("expectedFire") is False:
        issues.append(
            "positiveCase.expectedFire=false — polarity inversion "
            "(positive case must fire the UC)."
        )
    if isinstance(nc, dict) and nc.get("expectedFire") is True:
        issues.append(
            "negativeCase.expectedFire=true — polarity inversion "
            "(negative case must not fire the UC)."
        )
    return issues


def _coherence_check(
    events: list[dict], literals: dict[str, set[str]]
) -> list[str]:
    """Return human-readable warnings where the SPL's ``index=`` /
    ``source=`` / ``sourcetype=`` literals do not appear anywhere in
    the positive fixture's events.

    * Wildcarded literals (containing ``*``) are skipped — the
      matching is structural, not glob-based, and we do not want to
      run the regex engine just to say "cisco:* matches cisco:asa".
    * Empty literal sets are skipped — nothing to coerce against.
    * We only compare the fields that the fixture actually carries;
      a missing ``sourcetype`` field in the events is not a warning,
      just a silence.
    """
    if not events:
        return []
    warnings: list[str] = []
    for field in ("index", "source", "sourcetype"):
        declared = {lit for lit in literals.get(field, set()) if "*" not in lit}
        if not declared:
            continue
        observed = {
            str(e.get(field)) for e in events if field in e and e.get(field)
        }
        if not observed:
            # Fixture does not surface that field at all — silent.
            continue
        if declared.isdisjoint(observed):
            warnings.append(
                f"SPL references {field}=" + ", ".join(sorted(declared))
                + f" but positive fixture events only carry {field}="
                + ", ".join(sorted(observed))
            )
    return warnings


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------


def _iter_uc_sidecars() -> list[Path]:
    return sorted(USE_CASES.glob("cat-*/uc-*.json"))


def _collect_records(known_techniques: set[str]) -> tuple[list[dict], dict]:
    records: list[dict] = []
    hard_failures = 0
    summary: dict[str, Any] = {
        "total_ucs_examined": 0,
        "total_ucs_with_controltest": 0,
        "total_ucs_with_attack_ref": 0,
        "total_attack_refs": 0,
        "distinct_attack_techniques": set(),
        "statuses": {
            STATUS_SIMULATED: 0,
            STATUS_PENDING: 0,
            STATUS_NO_FIXTURE: 0,
            STATUS_POLARITY_FAIL: 0,
            STATUS_HEURISTIC_MISMATCH: 0,
        },
        "bad_technique_format_total": 0,
        "unknown_technique_total": 0,
        "hard_failures": 0,
    }

    for sidecar in _iter_uc_sidecars():
        try:
            uc = _load_json(sidecar)
        except (OSError, json.JSONDecodeError):
            # Broken sidecars are surfaced by audit_compliance_mappings.
            continue

        if not isinstance(uc, dict):
            continue

        summary["total_ucs_examined"] += 1
        uc_id = uc.get("id") or sidecar.stem.removeprefix("uc-")
        control_test = uc.get("controlTest")
        if not isinstance(control_test, dict):
            # No controlTest block → not a simulation candidate.
            continue

        summary["total_ucs_with_controltest"] += 1

        attack_refs = _collect_uc_technique_refs(uc)
        bad_format, unknown = _validate_technique_ids(attack_refs, known_techniques)
        has_attack = bool(attack_refs)
        if has_attack:
            summary["total_ucs_with_attack_ref"] += 1
        summary["total_attack_refs"] += len(attack_refs)
        summary["distinct_attack_techniques"].update(
            r for r in attack_refs if ATTACK_ID_RE.match(r)
        )

        fixture_ref = control_test.get("fixtureRef")
        fixture_path: Path | None = None
        fixture_status_note = None
        pos_events: list[dict] = []
        neg_events: list[dict] = []
        fixture_shape = None
        polarity_issues: list[str] = []
        coherence_warnings: list[str] = []

        if isinstance(fixture_ref, str) and fixture_ref:
            fixture_path = REPO / fixture_ref
            if fixture_path.is_file():
                try:
                    fixture = _load_json(fixture_path)
                except (OSError, json.JSONDecodeError) as err:
                    fixture_status_note = f"fixture parse error: {err}"
                    fixture = None
                if isinstance(fixture, dict):
                    pos_events, neg_events, fixture_shape = _fixture_events(fixture)
                    polarity_issues = _check_polarity(fixture, fixture_shape)
                elif fixture is not None:
                    fixture_status_note = (
                        f"fixture top-level is {type(fixture).__name__}, "
                        f"expected object"
                    )
            else:
                fixture_status_note = "fixture file not found on disk"

        # Decide the record's status.
        if polarity_issues:
            status = STATUS_POLARITY_FAIL
        elif not fixture_ref:
            status = STATUS_NO_FIXTURE
        elif fixture_path is None or fixture_status_note:
            status = STATUS_PENDING  # fixture declared but unreadable
        elif not pos_events and not neg_events:
            status = STATUS_PENDING
        elif not pos_events or not neg_events:
            status = STATUS_PENDING
        else:
            # Populated fixture — run the coherence heuristic.
            literals = _extract_spl_literals(uc.get("spl", ""))
            coherence_warnings = _coherence_check(pos_events, literals)
            status = (
                STATUS_HEURISTIC_MISMATCH if coherence_warnings else STATUS_SIMULATED
            )

        summary["statuses"][status] = summary["statuses"].get(status, 0) + 1
        if status in HARD_FAIL_STATUSES:
            hard_failures += 1

        if bad_format:
            summary["bad_technique_format_total"] += len(bad_format)
            hard_failures += len(bad_format)
        if unknown:
            summary["unknown_technique_total"] += len(unknown)
            hard_failures += len(unknown)

        records.append(
            {
                "uc_id": uc_id,
                "sidecar": str(sidecar.relative_to(REPO)),
                "attack_techniques": attack_refs,
                "bad_technique_format": bad_format,
                "unknown_techniques": unknown,
                "fixtureRef": fixture_ref if isinstance(fixture_ref, str) else None,
                "fixture_shape": fixture_shape,
                "pos_events": len(pos_events),
                "neg_events": len(neg_events),
                "status": status,
                "polarity_issues": polarity_issues,
                "coherence_warnings": coherence_warnings,
                "fixture_status_note": fixture_status_note,
                "has_attack_ref": has_attack,
            }
        )

    summary["hard_failures"] = hard_failures
    summary["distinct_attack_techniques"] = sorted(
        summary["distinct_attack_techniques"]
    )
    records.sort(key=lambda r: (r["uc_id"], r["sidecar"]))
    return records, summary


def _render_report(records: list[dict], summary: dict) -> str:
    payload = {
        "$comment": (
            "Phase 4.5d ATT&CK simulation report. Generated by "
            "scripts/simulate_controltest.py. Hard failures (bad "
            "technique IDs, unknown techniques, fixture polarity "
            "inversion) block CI; pending-fixture entries are tracked "
            "gaps for Phase 5.2 SME review. See docs/peer-review-guide.md "
            "\u00a73.2 for the assurance contract."
        ),
        "records": records,
        "summary": summary,
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _print_human_summary(records: list[dict], summary: dict) -> None:
    print("=== ATT&CK simulation gate ===")
    print(f"Total UC sidecars examined           : {summary['total_ucs_examined']}")
    print(f"UCs with a controlTest block         : {summary['total_ucs_with_controltest']}")
    print(f"UCs referencing an ATT&CK technique  : {summary['total_ucs_with_attack_ref']}")
    print(f"Distinct ATT&CK techniques referenced: {len(summary['distinct_attack_techniques'])}")
    print()
    print("Simulation status distribution :")
    for status in sorted(summary["statuses"].keys()):
        count = summary["statuses"][status]
        if count:
            print(f"  {status:<24} {count}")
    print()
    print(f"Bad technique IDs           : {summary['bad_technique_format_total']}")
    print(f"Unknown techniques (not MITRE): {summary['unknown_technique_total']}")
    print(f"Hard failures (CI blocker)  : {summary['hard_failures']}")

    hard_recs = [
        r
        for r in records
        if r["status"] in HARD_FAIL_STATUSES
        or r["bad_technique_format"]
        or r["unknown_techniques"]
    ]
    if hard_recs:
        print()
        print("Hard failures:")
        for rec in hard_recs:
            print(f"  {rec['uc_id']:<12} ({rec['status']})")
            for issue in rec["polarity_issues"]:
                print(f"    - polarity: {issue}")
            for ref in rec["bad_technique_format"]:
                print(f"    - bad ATT&CK ID format: {ref}")
            for ref in rec["unknown_techniques"]:
                print(f"    - unknown ATT&CK ID: {ref}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4.5d ATT&CK simulation gate."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the regenerated report to the committed "
        "reports/attack-simulation.json and exit non-zero on drift.",
    )
    args = parser.parse_args(argv)

    try:
        known = _load_known_techniques()
    except (FileNotFoundError, RuntimeError) as err:
        sys.stderr.write(f"ERROR: {err}\n")
        return 1

    records, summary = _collect_records(known)
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
                "ERROR: attack-simulation.json is out of date. "
                "Run `python3 scripts/simulate_controltest.py` and "
                "commit the updated report.\n"
            )
            return 1
    else:
        REPORT_PATH.write_text(payload_str, encoding="utf-8")

    _print_human_summary(records, summary)
    print()
    if summary["hard_failures"]:
        print("=== ATT&CK GATE: RED ===")
        return 1
    print("=== ATT&CK GATE: GREEN ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
