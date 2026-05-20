#!/usr/bin/env python3
"""Content quality audit — flags description==value duplicates, jargon in grandmaExplanation,
broken fixtureRefs, and heuristic gaps in ``description`` / ``value`` prose.

Lane N (maintainers) drain the surfaced queue by handwriting better text.
This audit never edits sidecars.

Outputs ``reports/content-quality-audit.json`` when ``--check`` or ``--report``
is used. Legacy ``--baseline`` / ``--generate-baseline`` modes preserve the
v1 violation list for backwards-compatible drift gating.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from splunk_uc.audits._content_quality_dimensions import (
    DescriptionFinding,
    ValueFinding,
    evaluate_description_quality,
    evaluate_value_quality,
)

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTENT_DIR = PROJECT_ROOT / "content"
REPORT_PATH = PROJECT_ROOT / "reports" / "content-quality-audit.json"
# Back-compat alias preserved for P16 wave GG tests (test_content_quality.py)
# which monkeypatch ``cq.SAMPLE_DATA`` to redirect fixtureRef resolution into
# a hermetic ``tmp_path / "sample-data"`` tree. B-6 source resolves
# ``fixtureRef`` against ``PROJECT_ROOT`` (which is also monkeypatched), so
# this symbol is documentation-only — its presence keeps
# ``monkeypatch.setattr(cq, "SAMPLE_DATA", ...)`` from raising AttributeError.
SAMPLE_DATA = PROJECT_ROOT / "sample-data"

JARGON_TERMS = [
    "tstats",
    "datamodel",
    "CIM",
    "sourcetype",
    "macro",
    "eval",
    "rex",
    "lookup",
    "savedsearch",
    "props.conf",
    "transforms.conf",
]

Severity = Literal["info", "warn", "fail"]
SEVERITY_RANK = {"info": 0, "warn": 1, "fail": 2}

FindingT = TypeVar("FindingT", DescriptionFinding, ValueFinding)


@dataclass(frozen=True)
class LegacyViolation:
    file: str
    id: str
    issue: str

    def to_json(self) -> dict[str, str]:
        return {"file": self.file, "id": self.id, "issue": self.issue}


def _iter_uc_paths(files: list[str] | None) -> list[pathlib.Path]:
    if files:
        paths: list[pathlib.Path] = []
        for raw in files:
            p = pathlib.Path(raw)
            if not p.is_absolute():
                p = PROJECT_ROOT / p
            paths.append(p)
        return sorted(paths)
    return sorted(CONTENT_DIR.rglob("UC-*.json"))


def _load_sidecar(uc_path: pathlib.Path) -> tuple[dict[str, Any] | None, LegacyViolation | None]:
    rel = str(uc_path.relative_to(PROJECT_ROOT))
    try:
        data = json.loads(uc_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, LegacyViolation(file=rel, id=uc_path.stem, issue="invalid_json")
    if not isinstance(data, dict):
        return None, LegacyViolation(file=rel, id=uc_path.stem, issue="invalid_json")
    return data, None


def _legacy_violations(data: dict[str, Any], rel: str, uc_id: str) -> list[LegacyViolation]:
    violations: list[LegacyViolation] = []

    if (
        data.get("description")
        and data.get("value")
        and str(data["description"]).strip() == str(data["value"]).strip()
    ):
        violations.append(
            LegacyViolation(file=rel, id=uc_id, issue="description_equals_value")
        )

    grandma = data.get("grandmaExplanation", "")
    if isinstance(grandma, str):
        for term in JARGON_TERMS:
            if term.lower() in grandma.lower():
                violations.append(
                    LegacyViolation(file=rel, id=uc_id, issue=f"jargon_in_grandma: {term}")
                )
                break

    ct = data.get("controlTest", {})
    if isinstance(ct, dict):
        ref = ct.get("fixtureRef", "")
        if isinstance(ref, str) and ref and not (PROJECT_ROOT / ref).exists():
            violations.append(
                LegacyViolation(file=rel, id=uc_id, issue=f"broken_fixtureRef: {ref}")
            )

    return violations


def _severity_at_least(finding_severity: Severity, threshold: Severity) -> bool:
    return SEVERITY_RANK[finding_severity] >= SEVERITY_RANK[threshold]


def _rollup_findings(
    description_findings: list[DescriptionFinding],
    value_findings: list[ValueFinding],
) -> dict[str, Any]:
    by_dimension: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    for finding in description_findings + value_findings:
        by_dimension[finding.dimension] += 1
        by_severity[finding.severity] += 1
    return {
        "description_total": len(description_findings),
        "value_total": len(value_findings),
        "combined_total": len(description_findings) + len(value_findings),
        "by_dimension": dict(sorted(by_dimension.items())),
        "by_severity": dict(sorted(by_severity.items())),
    }


def _build_report(
    *,
    scanned_ucs: int,
    legacy_violations: list[LegacyViolation],
    description_findings: list[DescriptionFinding],
    value_findings: list[ValueFinding],
) -> dict[str, Any]:
    summary = _rollup_findings(description_findings, value_findings)
    summary["legacy_violations"] = len(legacy_violations)
    return {
        "$comment": (
            "Content quality audit report. Description/value findings are "
            "heuristic queues for Lane N — not hard schema failures."
        ),
        "schema_version": "2.0",
        "scanned_ucs": scanned_ucs,
        "findings_summary": summary,
        "legacy_violations": [v.to_json() for v in legacy_violations],
        "description_findings": [f.to_json() for f in description_findings],
        "value_findings": [f.to_json() for f in value_findings],
    }


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def audit_corpus(
    *,
    files: list[str] | None = None,
    include_description: bool = True,
    include_value: bool = True,
) -> tuple[int, list[LegacyViolation], list[DescriptionFinding], list[ValueFinding]]:
    legacy: list[LegacyViolation] = []
    description_findings: list[DescriptionFinding] = []
    value_findings: list[ValueFinding] = []
    scanned = 0

    for uc_path in _iter_uc_paths(files):
        data, parse_violation = _load_sidecar(uc_path)
        if parse_violation is not None:
            legacy.append(parse_violation)
            continue
        assert data is not None
        scanned += 1
        uc_id = str(data.get("id", uc_path.stem.replace("UC-", "")))
        rel = str(uc_path.relative_to(PROJECT_ROOT))

        legacy.extend(_legacy_violations(data, rel, uc_id))

        if include_description:
            description_findings.extend(
                evaluate_description_quality(data, uc_id=uc_id)
            )
        if include_value:
            value_findings.extend(evaluate_value_quality(data, uc_id=uc_id))

    return scanned, legacy, description_findings, value_findings


def _filter_by_severity(
    findings: list[FindingT],
    threshold: Severity | None,
) -> list[FindingT]:
    if threshold is None:
        return findings
    return [f for f in findings if _severity_at_least(f.severity, threshold)]


def _print_legacy_result(new_violations: list[LegacyViolation], total: int) -> int:
    if new_violations:
        print(
            f"Content quality: {len(new_violations)} new violation(s):",
            file=sys.stderr,
        )
        for v in new_violations[:20]:
            print(f"  {v.file}: {v.issue}", file=sys.stderr)
        if len(new_violations) > 20:
            print(f"  ... and {len(new_violations) - 20} more", file=sys.stderr)
        return 1
    print(f"Content quality: {total} existing violation(s) (all in baseline), 0 new.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=str,
        help="Path to baseline file (existing legacy violations to ignore)",
    )
    parser.add_argument(
        "--generate-baseline",
        action="store_true",
        help="Output current legacy violations as baseline JSON",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Limit scan to specific UC sidecar path(s) (lift-loop per-UC gate)",
    )
    parser.add_argument(
        "--include-description",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run description quality heuristics (default: on)",
    )
    parser.add_argument(
        "--include-value",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run value quality heuristics (default: on)",
    )
    parser.add_argument(
        "--severity",
        choices=("info", "warn", "fail"),
        default=None,
        help="Only surface findings at or above this severity for exit-code gating",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=None,
        help=(
            "When set with --check, exit 0 if surfaced findings are at or below "
            "this count (generous CI ratchet cap)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write/compare reports/content-quality-audit.json and apply severity gate",
    )
    parser.add_argument(
        "--report",
        type=str,
        nargs="?",
        const=str(REPORT_PATH),
        default=None,
        help="Write JSON report (default path: reports/content-quality-audit.json)",
    )
    args = parser.parse_args(argv)

    scanned, legacy, description_findings, value_findings = audit_corpus(
        files=args.files,
        include_description=args.include_description,
        include_value=args.include_value,
    )

    if args.generate_baseline:
        json.dump([v.to_json() for v in legacy], sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    report = _build_report(
        scanned_ucs=scanned,
        legacy_violations=legacy,
        description_findings=description_findings,
        value_findings=value_findings,
    )

    report_path = pathlib.Path(args.report) if args.report else None
    if args.check or report_path is not None:
        target = report_path or REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        rendered = _canonical_json(report)
        target.write_text(rendered, encoding="utf-8")
        if args.check:
            try:
                rel_target = target.relative_to(PROJECT_ROOT)
            except ValueError:
                rel_target = target
            print(f"Content quality: wrote {rel_target}")

    if args.baseline:
        bp = pathlib.Path(args.baseline)
        baseline_ids: set[tuple[str, str]] = set()
        if bp.exists():
            baseline_ids = {
                (v["file"], v["issue"]) for v in json.loads(bp.read_text(encoding="utf-8"))
            }
        new_violations = [
            v for v in legacy if (v.file, v.issue) not in baseline_ids
        ]
        return _print_legacy_result(new_violations, len(legacy))

    if args.check or args.severity is not None or args.max_findings is not None:
        threshold: Severity | None = args.severity or "fail"
        desc_surfaced = _filter_by_severity(description_findings, threshold)
        val_surfaced = _filter_by_severity(value_findings, threshold)
        surfaced_count = len(desc_surfaced) + len(val_surfaced)
        if args.files:
            legacy_surface = legacy
        else:
            legacy_surface = [v for v in legacy if v.issue != "invalid_json"]
        total_surface = surfaced_count + len(legacy_surface)
        summary = report["findings_summary"]
        print(
            "Content quality summary: "
            f"scanned={scanned} "
            f"legacy={summary['legacy_violations']} "
            f"description={summary['description_total']} "
            f"value={summary['value_total']} "
            f"surfaced={total_surface}"
        )
        if args.max_findings is not None and total_surface > args.max_findings:
            print(
                f"Content quality: {total_surface} surfaced finding(s) exceed "
                f"--max-findings {args.max_findings}",
                file=sys.stderr,
            )
            return 1
        if args.files and (legacy_surface or surfaced_count):
            print(
                f"Content quality: {len(legacy_surface)} legacy + {surfaced_count} "
                "description/value finding(s) in scoped file(s)",
                file=sys.stderr,
            )
            return 1
        if args.severity == "fail" and surfaced_count and args.max_findings is None:
            print(
                f"Content quality: {surfaced_count} description/value finding(s) "
                "at or above fail",
                file=sys.stderr,
            )
            return 1
        return 0

    if legacy:
        return _print_legacy_result(legacy, len(legacy))

    print(
        f"Content quality: OK ({scanned} sidecars scanned, "
        "0 existing violation(s))."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
