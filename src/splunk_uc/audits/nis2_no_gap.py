#!/usr/bin/env python3
"""Audit the NIS2 no-gap obligation matrix.

The NIS2 expansion deliberately separates legal compliance from Splunk
monitoring evidence. This audit checks that the source matrix is complete
enough to support that distinction: every row must have source traceability,
a coverage decision, evidence, an owner, assurance rationale, review
confidence, and a concrete boundary statement.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO_ROOT / "data" / "per-regulation" / "nis2-coverage-expansion.json"
SOURCE_MAP_PATH = REPO_ROOT / "data" / "nis2-source-map.json"
CONTENT_ROOT = REPO_ROOT / "content"

VALID_COVERAGE = {"direct", "partial", "contributing", "not-monitorable"}
VALID_ASSURANCE = {"full", "partial", "contributing", "not-monitorable"}
VALID_CONFIDENCE = {
    "official-text-clear",
    "guidance-supported",
    "engineering-judgement",
    "requires-legal-review",
}
VALID_UC_PLAN = {
    "reuse existing UC",
    "uplift existing UC",
    "create new UC",
    "not-monitorable with supporting workflow",
}

REQUIRED_ROW_FIELDS = [
    "id",
    "source",
    "sourceUrl",
    "sourceType",
    "sourceAuthority",
    "retrieved",
    "bindingStatus",
    "clause",
    "obligation",
    "splunkCoverageType",
    "splunkCanDo",
    "splunkCannotDo",
    "dataSources",
    "ucPlan",
    "evidenceArtifact",
    "assuranceTarget",
    "assuranceRationale",
    "owner",
    "references",
    "reviewConfidence",
    "bestInClassRationale",
]


def _load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_nis2_compliance_entries() -> list[tuple[str, str, dict[str, Any]]]:
    entries: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(CONTENT_ROOT.glob("cat-*/UC-*.json")):
        try:
            doc = _load_json(path)
        except Exception:
            continue
        for entry in doc.get("compliance", []) or []:
            if str(entry.get("regulation", "")).strip().lower() == "nis2":
                entries.append(
                    (str(doc.get("id", path.stem)), str(path.relative_to(REPO_ROOT)), entry)
                )
    return entries


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _validate_matrix(matrix: dict[str, Any], source_map: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rows = matrix.get("coverageRows")
    if not isinstance(rows, list) or not rows:
        return ["matrix has no coverageRows"]

    source_urls = {
        src.get("url")
        for src in source_map.get("sources", [])
        if isinstance(src, dict) and src.get("url")
    }

    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        label = row.get("id") or f"row-{index}"
        if label in seen_ids:
            errors.append(f"{label}: duplicate id")
        seen_ids.add(str(label))

        for field in REQUIRED_ROW_FIELDS:
            if not _is_non_empty(row.get(field)):
                errors.append(f"{label}: missing {field}")

        if row.get("splunkCoverageType") not in VALID_COVERAGE:
            errors.append(f"{label}: invalid splunkCoverageType {row.get('splunkCoverageType')!r}")
        if row.get("assuranceTarget") not in VALID_ASSURANCE:
            errors.append(f"{label}: invalid assuranceTarget {row.get('assuranceTarget')!r}")
        if row.get("reviewConfidence") not in VALID_CONFIDENCE:
            errors.append(f"{label}: invalid reviewConfidence {row.get('reviewConfidence')!r}")
        if row.get("ucPlan") not in VALID_UC_PLAN:
            errors.append(f"{label}: invalid ucPlan {row.get('ucPlan')!r}")

        refs = row.get("references") or []
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label}: references must be a non-empty list")
        else:
            first = refs[0]
            if not isinstance(first, dict) or first.get("type") not in {
                "binding-law",
                "official-guidance",
                "national-guidance",
            }:
                errors.append(f"{label}: first reference must be official or national guidance")

        source_url = row.get("sourceUrl")
        if source_url and source_url not in source_urls:
            errors.append(f"{label}: sourceUrl not present in data/nis2-source-map.json")

        cannot = str(row.get("splunkCannotDo", "")).lower()
        if "n/a" in cannot or "none" == cannot.strip():
            errors.append(f"{label}: splunkCannotDo must state a real boundary")

        evidence = str(row.get("evidenceArtifact", "")).lower()
        if "monitor manually" in evidence:
            errors.append(f"{label}: evidenceArtifact contains vague manual-monitoring wording")

    required_groups = {
        "directive",
        "commission-implementing-regulation-2024-2690",
        "enisa-guidance",
        "national-guidance",
        "sector-overlay",
    }
    present_groups = {str(row.get("source")) for row in rows}
    missing_groups = sorted(required_groups - present_groups)
    for group in missing_groups:
        errors.append(f"matrix missing required source group {group}")

    required_clauses = {
        "Art.20(1)",
        "Art.20(2)",
        "Art.21(2)(a)",
        "Art.21(2)(j)",
        "Art.23(4)(a)",
        "Annex 3.2",
        "Annex I",
        "Annex II",
    }
    present_clauses = {str(row.get("clause")) for row in rows}
    for clause in sorted(required_clauses - present_clauses):
        errors.append(f"matrix missing required high-value clause {clause}")

    return errors


def _validate_uc_traceability(matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    matrix_clauses = {str(row.get("clause")) for row in matrix.get("coverageRows", [])}
    for uc_id, path, entry in _iter_nis2_compliance_entries():
        clause = str(entry.get("clause", "")).strip()
        if not clause:
            errors.append(f"UC-{uc_id} {path}: empty NIS2 clause")
        if not entry.get("clauseUrl"):
            errors.append(f"UC-{uc_id} {path}: NIS2 entry {clause} missing clauseUrl")
        if not entry.get("controlObjective"):
            errors.append(f"UC-{uc_id} {path}: NIS2 entry {clause} missing controlObjective")
        if not entry.get("evidenceArtifact"):
            errors.append(f"UC-{uc_id} {path}: NIS2 entry {clause} missing evidenceArtifact")
        if clause and clause not in matrix_clauses:
            errors.append(f"UC-{uc_id} {path}: NIS2 clause {clause} is not in matrix")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable audit result")
    args = parser.parse_args(argv)

    errors: list[str] = []
    if not MATRIX_PATH.exists():
        errors.append(f"missing {MATRIX_PATH.relative_to(REPO_ROOT)}")
    if not SOURCE_MAP_PATH.exists():
        errors.append(f"missing {SOURCE_MAP_PATH.relative_to(REPO_ROOT)}")

    matrix: dict[str, Any] = {}
    source_map: dict[str, Any] = {}
    if not errors:
        matrix = _load_json(MATRIX_PATH)
        source_map = _load_json(SOURCE_MAP_PATH)
        errors.extend(_validate_matrix(matrix, source_map))
        errors.extend(_validate_uc_traceability(matrix))

    payload: dict[str, Any] = {
        "status": "passed" if not errors else "failed",
        "matrixRows": len(matrix.get("coverageRows", [])) if matrix else 0,
        "nis2ComplianceEntries": len(_iter_nis2_compliance_entries()),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "NIS2 no-gap audit: "
            f"{payload['status'].upper()}  rows={payload['matrixRows']}  "
            f"nis2_entries={payload['nis2ComplianceEntries']}  errors={len(errors)}"
        )
        for err in errors[:50]:
            print(f"  - {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
