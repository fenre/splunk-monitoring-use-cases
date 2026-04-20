#!/usr/bin/env python3
"""Augment ``api/v1/compliance/regulations/*.json`` with story-layer fields.

Introduced by the Regulation-to-UC Story Redesign (Phase 2b). Reads the
reverse-index artefacts emitted by ``scripts/generate_clause_index.py``
and injects per-version ``clauseCoverageMatrix[]`` plus correctly-populated
``clausesReferencedByCatalogue[]`` and ``useCasesTaggingThisVersion[]``
into every regulation and per-version-slice file already on disk.

Why a post-processor rather than an extension of
``scripts/generate_api_surface.py``: the existing generator's UC glob still
points at the legacy ``use-cases/cat-*/uc-*.json`` tree (now empty — the
catalogue moved to ``content/cat-*/UC-*.json`` in v4+) and so it writes
empty ``useCasesTaggingThisVersion[]`` / ``clausesReferencedByCatalogue[]``
arrays. Migrating the upstream generator's UC loader is orthogonal to this
plan; augmenting here keeps the blast radius to regulation endpoints and
matches the incremental pattern used for equipment and scorecard data.

Inputs (in-repo, zero network):

* ``api/v1/compliance/clauses/index.json``     — clause registry (Phase 2a).
* ``api/v1/compliance/clauses/*.json``         — per-clause detail (Phase 2a).
* ``api/v1/compliance/regulations/*.json``     — emitted by
                                                  ``generate_api_surface.py``;
                                                  updated in place.
* ``data/regulations.json``                    — master framework registry.

Outputs: same regulation files, but each version object gains:

* ``clauseCoverageMatrix[]``       — one row per ``commonClauses[]`` entry
                                     (with any off-list clauses tagged by
                                     UCs appended), each carrying
                                     ``clause``, ``topic``, ``priorityWeight``,
                                     ``obligationText``, ``coveringUcs[]``,
                                     ``topAssurance`` and ``coverageState``
                                     (``covered-full`` / ``covered-partial``
                                     / ``contributing-only`` / ``uncovered``).
* ``clausesReferencedByCatalogue`` — populated from the reverse index.
* ``useCasesTaggingThisVersion``   — populated from the reverse index.
* ``coverageSummary``              — totals per ``coverageState`` label plus
                                     priority-weighted coverage percentage.

Design invariants mirror ``scripts/generate_api_surface.py`` and
``scripts/generate_clause_index.py``:

* Deterministic JSON (``sort_keys=True``, ``indent=2``, UTF-8, trailing
  newline, sorted lists).
* ``--check`` mode regenerates into a temp tree and diffs against the
  committed files; exits non-zero on drift.

Exit codes:
    0  Success.
    1  Drift / missing input.
    2  Uncaught exception.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import sys
import tempfile
import urllib.parse
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CLAUSES_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "clauses"
REGS_DIR = REPO_ROOT / "api" / "v1" / "compliance" / "regulations"
REGULATIONS_PATH = REPO_ROOT / "data" / "regulations.json"


# ---------------------------------------------------------------------------
# IO helpers (kept identical in contract to the other generators)
# ---------------------------------------------------------------------------


def _load_json(path: pathlib.Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Index / registry loaders
# ---------------------------------------------------------------------------


def load_clause_index(clauses_dir: Optional[pathlib.Path] = None) -> List[Dict[str, Any]]:
    """Load the clause registry produced by ``generate_clause_index.py``.

    ``clauses_dir`` defaults to ``api/v1/compliance/clauses`` so ad-hoc
    callers keep the old behaviour.  ``generate_api_surface.py`` passes
    a temp-rooted path so ``--check`` can compare a freshly-rendered
    tree without touching the committed workspace.
    """
    base = clauses_dir or CLAUSES_DIR
    path = base / "index.json"
    if not path.exists():
        raise SystemExit(
            f"ERROR: {path} missing. "
            "Run scripts/generate_clause_index.py first."
        )
    idx = _load_json(path)
    rows = idx.get("clauses") or []
    if not isinstance(rows, list):
        raise SystemExit(f"ERROR: {path} has no 'clauses' array")
    return rows


def group_clauses_by_regulation_version(
    clauses: Iterable[Mapping[str, Any]],
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    out: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in clauses:
        reg = row.get("regulationId")
        ver = row.get("version")
        if not isinstance(reg, str) or not isinstance(ver, str):
            continue
        out[(reg, ver)].append(dict(row))
    return out


# ---------------------------------------------------------------------------
# Coverage computations
# ---------------------------------------------------------------------------


_ASSURANCE_RANK = {"full": 3, "partial": 2, "contributing": 1}


def _coverage_state_from_assurance(top: Optional[str]) -> str:
    if top == "full":
        return "covered-full"
    if top == "partial":
        return "covered-partial"
    if top == "contributing":
        return "contributing-only"
    return "uncovered"


def build_clause_coverage_matrix(
    version_obj: Mapping[str, Any],
    reg_rows: List[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge the framework's declared ``commonClauses[]`` with any clauses
    the catalogue actually tags for this version, then annotate each row.

    Rows derived from ``commonClauses[]`` drive the coverage %; rows
    appended from off-list UC-tagged clauses carry ``offCommonList: true``
    so the auditor view can render them separately.
    """
    rows_by_clause: Dict[str, Dict[str, Any]] = {}
    for cc in version_obj.get("commonClauses") or []:
        clause = cc.get("clause")
        if not isinstance(clause, str):
            continue
        rows_by_clause[clause] = {
            "clause": clause,
            "topic": cc.get("topic"),
            "priorityWeight": cc.get("priorityWeight"),
            "obligationText": cc.get("obligationText"),
            "obligationSource": cc.get("obligationSource"),
            "onCommonList": True,
            "coveringUcs": [],
            "topAssurance": None,
            "coverageState": "uncovered",
            "assuranceBreakdown": {"full": 0, "partial": 0, "contributing": 0},
        }

    for row in reg_rows:
        clause = row.get("clause")
        if not isinstance(clause, str):
            continue
        entry = rows_by_clause.get(clause)
        if entry is None:
            entry = {
                "clause": clause,
                "topic": row.get("topic"),
                "priorityWeight": row.get("priorityWeight"),
                "obligationText": None,
                "obligationSource": None,
                "onCommonList": False,
                "coveringUcs": [],
                "topAssurance": None,
                "coverageState": "uncovered",
                "assuranceBreakdown": {"full": 0, "partial": 0, "contributing": 0},
            }
            rows_by_clause[clause] = entry
        covering = row.get("coveringUcs") or []
        entry["coveringUcs"] = sorted(set(entry["coveringUcs"]) | set(covering))
        ab = row.get("assuranceBreakdown") or {}
        for level in ("full", "partial", "contributing"):
            entry["assuranceBreakdown"][level] += int(ab.get(level) or 0)
        state = row.get("coverageState")
        top = row.get("topAssurance")
        entry["topAssurance"] = _better_assurance(entry["topAssurance"], top)
        entry["coverageState"] = _stronger_coverage_state(
            entry["coverageState"], state
        )

    for entry in rows_by_clause.values():
        if not entry["coveringUcs"]:
            entry["coverageState"] = "uncovered"
            entry["topAssurance"] = None
        elif entry["topAssurance"] and entry["coverageState"] == "uncovered":
            entry["coverageState"] = _coverage_state_from_assurance(
                entry["topAssurance"]
            )

    return sorted(rows_by_clause.values(), key=lambda r: (not r["onCommonList"], r["clause"]))


def _better_assurance(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if not a:
        return b
    if not b:
        return a
    return a if _ASSURANCE_RANK.get(a, 0) >= _ASSURANCE_RANK.get(b, 0) else b


_STATE_RANK = {
    "uncovered": 0,
    "contributing-only": 1,
    "covered-partial": 2,
    "covered-full": 3,
}


def _stronger_coverage_state(a: Optional[str], b: Optional[str]) -> str:
    """Pick the stronger of two coverage-state labels."""
    ra = _STATE_RANK.get(a or "uncovered", 0)
    rb = _STATE_RANK.get(b or "uncovered", 0)
    return a if ra >= rb else b  # type: ignore[return-value]


def build_coverage_summary(matrix: List[Mapping[str, Any]]) -> Dict[str, Any]:
    state_counts = {"covered-full": 0, "covered-partial": 0, "contributing-only": 0, "uncovered": 0}
    total_weight = 0.0
    covered_weight = 0.0  # full=1.0x, partial=0.5x, contributing=0.25x, uncovered=0
    on_common_rows = [r for r in matrix if r.get("onCommonList")]
    for r in on_common_rows:
        state_counts[r.get("coverageState", "uncovered")] = (
            state_counts.get(r.get("coverageState", "uncovered"), 0) + 1
        )
        pw = float(r.get("priorityWeight") or 0.0)
        total_weight += pw
        ta = r.get("topAssurance")
        if ta == "full":
            covered_weight += pw * 1.0
        elif ta == "partial":
            covered_weight += pw * 0.5
        elif ta == "contributing":
            covered_weight += pw * 0.25
    total_common = len(on_common_rows)
    covered_any = sum(
        1
        for r in on_common_rows
        if r.get("coverageState") != "uncovered"
    )
    return {
        "commonClauseCount": total_common,
        "coveredClauseCount": covered_any,
        "stateCounts": state_counts,
        "clauseCoveragePercent": round(
            (100.0 * covered_any / total_common) if total_common else 0.0, 2
        ),
        "priorityWeightedCoveragePercent": round(
            (100.0 * covered_weight / total_weight) if total_weight else 0.0, 2
        ),
        "offCommonListClauseCount": sum(
            1 for r in matrix if not r.get("onCommonList") and r.get("coveringUcs")
        ),
    }


# ---------------------------------------------------------------------------
# File-name resolution
# ---------------------------------------------------------------------------


_VERSION_SLUG_RX = re.compile(r"[/\s]")


def version_slug(version: str) -> str:
    """Match the convention used by ``generate_api_surface.py`` — ``/`` and
    whitespace → ``-``, everything else URL-encoded.
    """
    return urllib.parse.quote(_VERSION_SLUG_RX.sub("-", version), safe="-._()")


# ---------------------------------------------------------------------------
# Main augmentation
# ---------------------------------------------------------------------------


def augment_regulation_file(
    reg_path: pathlib.Path,
    rows_by_rv: Dict[Tuple[str, str], List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Augment one multi-version regulation file in place.

    Returns ``{version_string: clauseCoverageMatrix_rows}`` so the caller
    can re-use the same matrices when updating the per-version slice
    files without recomputing.
    """
    payload = _load_json(reg_path)
    reg_id = payload.get("id")
    if not isinstance(reg_id, str):
        return {}
    versions = payload.get("versions") or []
    if not isinstance(versions, list):
        return {}
    matrices: Dict[str, List[Dict[str, Any]]] = {}
    for v in versions:
        if not isinstance(v, Mapping):
            continue
        ver_str = v.get("version")
        if not isinstance(ver_str, str):
            continue
        rows = rows_by_rv.get((reg_id, ver_str), [])
        matrix = build_clause_coverage_matrix(v, rows)
        matrices[ver_str] = matrix
        # UCs tagging this version (unique, sorted)
        ucs = sorted({uc for row in matrix for uc in row["coveringUcs"]})
        referenced = sorted({row["clause"] for row in matrix if row["coveringUcs"]})
        v["clausesReferencedByCatalogue"] = referenced
        v["useCasesTaggingThisVersion"] = ucs
        v["clauseCoverageMatrix"] = matrix
        v["coverageSummary"] = build_coverage_summary(matrix)
    _write_json(reg_path, payload)
    return matrices


def augment_single_version_file(
    slice_path: pathlib.Path,
    reg_id: str,
    matrices: Dict[str, List[Dict[str, Any]]],
    version_str: str,
) -> None:
    """Augment the ``regulations/{id}@{version}.json`` slice file to match."""
    if not slice_path.exists():
        return
    payload = _load_json(slice_path)
    ver_obj = payload.get("version")
    if not isinstance(ver_obj, Mapping):
        return
    rows = matrices.get(version_str, [])
    ucs = sorted({uc for row in rows for uc in row["coveringUcs"]})
    referenced = sorted({row["clause"] for row in rows if row["coveringUcs"]})
    ver_obj["clausesReferencedByCatalogue"] = referenced
    ver_obj["useCasesTaggingThisVersion"] = ucs
    ver_obj["clauseCoverageMatrix"] = rows
    ver_obj["coverageSummary"] = build_coverage_summary(rows)
    _write_json(slice_path, payload)


def augment_regulations_index(
    reg_root: pathlib.Path,
    rows_by_rv: Dict[Tuple[str, str], List[Dict[str, Any]]],
) -> None:
    """Append a ``catalogueCoverageSummary`` to ``regulations/index.json``."""
    idx_path = reg_root / "index.json"
    if not idx_path.exists():
        return
    idx = _load_json(idx_path)
    summary_by_framework: Dict[str, Any] = {}
    for fw in idx.get("frameworks", []):
        if not isinstance(fw, Mapping):
            continue
        reg_id = fw.get("id")
        if not isinstance(reg_id, str):
            continue
        # Load the already-augmented per-regulation file to read its summaries
        per_reg = _load_json(reg_root / f"{reg_id}.json")
        totals = {
            "commonClauseCount": 0,
            "coveredClauseCount": 0,
            "uncoveredClauseCount": 0,
            "priorityWeightedCoverageMean": 0.0,
        }
        pw_vals = []
        for v in per_reg.get("versions") or []:
            s = v.get("coverageSummary") or {}
            totals["commonClauseCount"] += int(s.get("commonClauseCount") or 0)
            totals["coveredClauseCount"] += int(s.get("coveredClauseCount") or 0)
            totals["uncoveredClauseCount"] += int(
                (s.get("commonClauseCount") or 0) - (s.get("coveredClauseCount") or 0)
            )
            pw = s.get("priorityWeightedCoveragePercent")
            if isinstance(pw, (int, float)):
                pw_vals.append(float(pw))
        if pw_vals:
            totals["priorityWeightedCoverageMean"] = round(
                sum(pw_vals) / len(pw_vals), 2
            )
        summary_by_framework[reg_id] = totals
    idx["catalogueCoverageSummary"] = summary_by_framework
    _write_json(idx_path, idx)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def augment_all(
    reg_root: Optional[pathlib.Path] = None,
    *,
    clauses_dir: Optional[pathlib.Path] = None,
) -> None:
    reg_root = reg_root or REGS_DIR
    if not reg_root.exists():
        try:
            rel = reg_root.relative_to(REPO_ROOT)
        except ValueError:
            rel = reg_root
        raise SystemExit(
            f"ERROR: {rel} missing. "
            "Run scripts/generate_api_surface.py first."
        )
    # When called from generate_api_surface.py we receive an explicit
    # clauses_dir rooted at the temp output tree; ad-hoc callers keep
    # the default ``api/v1/compliance/clauses`` path.
    if clauses_dir is None and reg_root != REGS_DIR:
        candidate = reg_root.parent / "clauses"
        if candidate.exists():
            clauses_dir = candidate
    clause_rows = load_clause_index(clauses_dir)
    rows_by_rv = group_clauses_by_regulation_version(clause_rows)

    matrices_by_reg: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for reg_path in sorted(reg_root.glob("*.json")):
        if "@" in reg_path.stem or reg_path.name == "index.json":
            continue
        pre_payload = _load_json(reg_path)
        reg_id = pre_payload.get("id")
        if not isinstance(reg_id, str):
            continue
        matrices = augment_regulation_file(reg_path, rows_by_rv) or {}
        matrices_by_reg[reg_id] = matrices
        for v in pre_payload.get("versions") or []:
            ver_str = v.get("version")
            if not isinstance(ver_str, str):
                continue
            slice_path = reg_root / f"{reg_id}@{version_slug(ver_str)}.json"
            augment_single_version_file(slice_path, reg_id, matrices, ver_str)

    augment_regulations_index(reg_root, rows_by_rv)


def _hash_tree(root: pathlib.Path) -> str:
    h = hashlib.sha256()
    if not root.exists():
        return h.hexdigest()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


def _check_drift() -> int:
    """Drift check: rerun the augmentation into a temp copy and diff."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp) / "regulations"
        shutil.copytree(REGS_DIR, tmp_root)
        augment_all(tmp_root)
        new_hash = _hash_tree(tmp_root)
    committed_hash = _hash_tree(REGS_DIR)
    if new_hash != committed_hash:
        print(
            "ERROR: api/v1/compliance/regulations/ is out of date. "
            "Run scripts/augment_regulation_api.py to regenerate.",
            file=sys.stderr,
        )
        return 1
    print(
        f"api/v1/compliance/regulations/ is up to date ({new_hash[:12]})",
        file=sys.stderr,
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Rerun augmentation in a temp tree and exit non-zero on drift.",
    )
    args = parser.parse_args(argv)
    if args.check:
        return _check_drift()
    try:
        augment_all()
    except SystemExit:
        raise
    except Exception as err:
        print(f"UNEXPECTED ERROR: {err!r}", file=sys.stderr)
        return 2
    print(
        "Augmented api/v1/compliance/regulations/ with clauseCoverageMatrix + UC/clause arrays.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
