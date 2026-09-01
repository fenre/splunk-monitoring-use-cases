#!/usr/bin/env python3
"""Audit NO KBF coverage matrix drift against UC sidecars and regulations.json."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
MATRIX_PATH = REPO_ROOT / "data" / "per-regulation" / "no-kbf-nve-coverage-expansion.json"
SOURCE_MAP_PATH = REPO_ROOT / "data" / "no-kbf-nve-source-map.json"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"
DUAL_MAP_PATH = REPO_ROOT / "data" / "no-kbf-nis2-dual-mapping.json"
CONTENT_ROOT = REPO_ROOT / "content"

VALID_COVERAGE = {"direct", "partial", "contributing", "not-monitorable"}
VALID_ASSURANCE = {"full", "partial", "contributing", "not-monitorable"}
VALID_CONFIDENCE = {
    "official-text-clear",
    "guidance-supported",
    "engineering-judgement",
    "requires-legal-review",
}

REQUIRED_ROW_FIELDS = [
    "id",
    "clause",
    "obligation",
    "controlFamily",
    "splunkCoverageType",
    "assuranceTarget",
    "assuranceRationale",
    "owner",
    "evidenceArtifact",
    "dataSources",
    "splunkCanDo",
    "splunkCannotDo",
    "reviewConfidence",
    "sourceUrl",
    "ucPlan",
    "targetUcIds",
]


def _load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _kbf_regulation() -> dict[str, Any] | None:
    for reg in _load_json(REGULATIONS_PATH).get("frameworks", []):
        if reg.get("id") == "no-kbf-nve":
            return reg
    return None


def _common_clauses(reg: dict[str, Any]) -> set[str]:
    clauses: set[str] = set()
    for version in reg.get("versions", []):
        for item in version.get("commonClauses", []):
            clause = str(item.get("clause", "")).strip()
            if clause:
                clauses.add(clause)
    return clauses


def _uc_path(uc_id: str) -> pathlib.Path | None:
    matches = list(CONTENT_ROOT.glob(f"cat-*/UC-{uc_id}.json"))
    return matches[0] if matches else None


def _iter_kbf_compliance_entries() -> list[tuple[str, str, dict[str, Any]]]:
    entries: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(CONTENT_ROOT.glob("cat-*/UC-*.json")):
        try:
            doc = _load_json(path)
        except Exception:
            continue
        uc_id = str(doc.get("id", path.stem.replace("UC-", "")))
        for entry in doc.get("compliance", []) or []:
            reg = str(entry.get("regulation", "")).strip().lower()
            if reg in {"no kbf", "no-kbf-nve", "kbf"}:
                entries.append((uc_id, str(path.relative_to(REPO_ROOT)), entry))
    return entries


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
    seen_clauses: set[str] = set()
    for index, row in enumerate(rows, start=1):
        label = str(row.get("id") or f"row-{index}")
        if label in seen_ids:
            errors.append(f"{label}: duplicate id")
        seen_ids.add(label)

        clause = str(row.get("clause", "")).strip()
        if clause:
            if clause in seen_clauses:
                errors.append(f"{label}: duplicate clause {clause}")
            seen_clauses.add(clause)

        for field in REQUIRED_ROW_FIELDS:
            if not _is_non_empty(row.get(field)):
                errors.append(f"{label}: missing {field}")

        if row.get("splunkCoverageType") not in VALID_COVERAGE:
            errors.append(f"{label}: invalid splunkCoverageType {row.get('splunkCoverageType')!r}")
        if row.get("assuranceTarget") not in VALID_ASSURANCE:
            errors.append(f"{label}: invalid assuranceTarget {row.get('assuranceTarget')!r}")
        if row.get("reviewConfidence") not in VALID_CONFIDENCE:
            errors.append(f"{label}: invalid reviewConfidence {row.get('reviewConfidence')!r}")

        source_url = row.get("sourceUrl")
        if source_url and source_url not in source_urls:
            errors.append(f"{label}: sourceUrl not present in data/no-kbf-nve-source-map.json")

        cannot = str(row.get("splunkCannotDo", "")).lower()
        if "n/a" in cannot or cannot.strip() == "none":
            errors.append(f"{label}: splunkCannotDo must state a real boundary")

        target_ids = row.get("targetUcIds") or []
        if not isinstance(target_ids, list):
            errors.append(f"{label}: targetUcIds must be a list")
        else:
            for uc_id in target_ids:
                if _uc_path(str(uc_id)) is None:
                    errors.append(f"{label}: targetUcIds references missing UC-{uc_id}")

    return errors


def _validate_regulation_alignment(matrix: dict[str, Any], reg: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    matrix_clauses = {str(row.get("clause")) for row in matrix.get("coverageRows", [])}
    reg_clauses = _common_clauses(reg)
    for clause in sorted(reg_clauses - matrix_clauses):
        errors.append(f"regulations.json commonClause {clause} missing from matrix")
    for clause in sorted(matrix_clauses - reg_clauses):
        errors.append(f"matrix clause {clause} missing from regulations.json commonClauses")
    return errors


def _iter_nis2_compliance_entries() -> list[tuple[str, str, dict[str, Any]]]:
    entries: list[tuple[str, str, dict[str, Any]]] = []
    for path in sorted(CONTENT_ROOT.glob("cat-*/UC-*.json")):
        try:
            doc = _load_json(path)
        except Exception:
            continue
        uc_id = str(doc.get("id", path.stem.replace("UC-", "")))
        for entry in doc.get("compliance", []) or []:
            if str(entry.get("regulation", "")).strip().lower() == "nis2":
                entries.append((uc_id, str(path.relative_to(REPO_ROOT)), entry))
    return entries


def _uc_compliance_clauses(uc_id: str, regulation: str) -> set[str]:
    path = _uc_path(uc_id)
    if path is None:
        return set()
    doc = _load_json(path)
    reg_norm = regulation.strip().lower()
    clauses: set[str] = set()
    for entry in doc.get("compliance", []) or []:
        reg = str(entry.get("regulation", "")).strip().lower()
        if reg_norm == "no kbf" and reg in {"no kbf", "no-kbf-nve", "kbf"}:
            clause = str(entry.get("clause", "")).strip()
            if clause:
                clauses.add(clause)
        elif reg_norm == "nis2" and reg == "nis2":
            clause = str(entry.get("clause", "")).strip()
            if clause:
                clauses.add(clause)
    return clauses


def _validate_dual_mapping(dual_map: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    mappings = dual_map.get("mappings")
    if not isinstance(mappings, list) or not mappings:
        return ["dual-mapping has no mappings"]

    review = dual_map.get("assuranceReview")
    if not isinstance(review, dict):
        errors.append("dual-mapping missing assuranceReview block")
    else:
        for field in ("reviewedOn", "reviewer", "policy", "outcome"):
            if not _is_non_empty(review.get(field)):
                errors.append(f"dual-mapping assuranceReview missing {field}")
        outcome = str(review.get("outcome", "")).strip().lower()
        if outcome and outcome not in {"approved", "approved-with-caveats"}:
            errors.append(f"dual-mapping assuranceReview invalid outcome {outcome!r}")

    dual_uc_ids: set[str] = set()
    for index, row in enumerate(mappings, start=1):
        label = f"{row.get('kbfClause', '?')}↔{row.get('nis2Clause', '?')}"
        for field in ("kbfClause", "nis2Clause", "topic", "rationale"):
            if not _is_non_empty(row.get(field)):
                errors.append(f"dual-mapping row {index} ({label}): missing {field}")
        primary = row.get("primaryUcIds") or []
        if not isinstance(primary, list) or not primary:
            errors.append(f"dual-mapping row {index} ({label}): primaryUcIds must be non-empty")
            continue
        kbf_clause = str(row.get("kbfClause", "")).strip()
        nis2_clause = str(row.get("nis2Clause", "")).strip()
        nis2_covered = False
        for uc_id in primary:
            uc_id = str(uc_id)
            dual_uc_ids.add(uc_id)
            if _uc_path(uc_id) is None:
                errors.append(f"dual-mapping row {index}: missing UC-{uc_id}")
                continue
            kbf_clauses = _uc_compliance_clauses(uc_id, "NO KBF")
            if kbf_clause and kbf_clause not in kbf_clauses:
                errors.append(
                    f"dual-mapping row {index}: UC-{uc_id} missing NO KBF compliance for {kbf_clause}"
                )
            nis2_clauses = _uc_compliance_clauses(uc_id, "nis2")
            if nis2_clause in nis2_clauses:
                nis2_covered = True
        if nis2_clause and not nis2_covered:
            errors.append(
                f"dual-mapping row {index} ({label}): no primary UC carries NIS2 {nis2_clause}"
            )

    for uc_id, path, entry in _iter_nis2_compliance_entries():
        if uc_id not in dual_uc_ids:
            continue
        assurance = str(entry.get("assurance", "")).strip().lower()
        if assurance == "full":
            errors.append(
                f"UC-{uc_id} {path}: dual-mapped NIS2 entry must not claim full assurance"
            )
        if assurance not in {"contributing", "partial"}:
            errors.append(
                f"UC-{uc_id} {path}: dual-mapped NIS2 assurance must be contributing or partial"
            )
    return errors


def _validate_uc_traceability(matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    matrix_by_clause: dict[str, dict[str, Any]] = {
        str(row.get("clause")): row for row in matrix.get("coverageRows", [])
    }

    covered: dict[str, set[str]] = {clause: set() for clause in matrix_by_clause}
    for uc_id, path, entry in _iter_kbf_compliance_entries():
        clause = str(entry.get("clause", "")).strip()
        if not clause:
            errors.append(f"UC-{uc_id} {path}: empty NO KBF clause")
            continue
        if clause not in matrix_by_clause:
            errors.append(f"UC-{uc_id} {path}: NO KBF clause {clause} is not in matrix")
            continue
        if not entry.get("controlObjective"):
            errors.append(f"UC-{uc_id} {path}: NO KBF entry {clause} missing controlObjective")
        if not entry.get("evidenceArtifact"):
            errors.append(f"UC-{uc_id} {path}: NO KBF entry {clause} missing evidenceArtifact")
        covered[clause].add(uc_id)

    for clause, row in matrix_by_clause.items():
        expected = {str(x) for x in row.get("targetUcIds") or []}
        actual = covered.get(clause, set())
        if expected != actual:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            if missing:
                errors.append(f"{clause}: matrix targetUcIds missing compliance on {', '.join(missing)}")
            if extra:
                errors.append(f"{clause}: compliance mapped on UCs not in matrix targetUcIds: {', '.join(extra)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable audit result")
    args = parser.parse_args(argv)

    errors: list[str] = []
    matrix: dict[str, Any] = {}
    if not MATRIX_PATH.exists():
        errors.append(f"missing {MATRIX_PATH.relative_to(REPO_ROOT)}")
    if not SOURCE_MAP_PATH.exists():
        errors.append(f"missing {SOURCE_MAP_PATH.relative_to(REPO_ROOT)}")
    if not REGULATIONS_PATH.exists():
        errors.append(f"missing {REGULATIONS_PATH.relative_to(REPO_ROOT)}")

    reg = _kbf_regulation()
    if reg is None:
        errors.append("regulations.json missing no-kbf-nve entry")

    if not errors:
        matrix = _load_json(MATRIX_PATH)
        source_map = _load_json(SOURCE_MAP_PATH)
        errors.extend(_validate_matrix(matrix, source_map))
        errors.extend(_validate_regulation_alignment(matrix, reg))
        errors.extend(_validate_uc_traceability(matrix))
        if DUAL_MAP_PATH.exists():
            errors.extend(_validate_dual_mapping(_load_json(DUAL_MAP_PATH)))
        else:
            errors.append(f"missing {DUAL_MAP_PATH.relative_to(REPO_ROOT)}")

    payload: dict[str, Any] = {
        "status": "passed" if not errors else "failed",
        "matrixRows": len(matrix.get("coverageRows", [])) if matrix else 0,
        "kbfComplianceEntries": len(_iter_kbf_compliance_entries()),
        "dualMappingRows": len(_load_json(DUAL_MAP_PATH).get("mappings", [])) if DUAL_MAP_PATH.exists() else 0,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "NO KBF coverage audit: "
            f"{payload['status'].upper()}  rows={payload['matrixRows']}  "
            f"kbf_entries={payload['kbfComplianceEntries']}  errors={len(errors)}"
        )
        for err in errors[:50]:
            print(f"  - {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
