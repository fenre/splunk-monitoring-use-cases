#!/usr/bin/env python3
"""Audit every UC's compliance[] mappings against the regulations catalogue.

Tier-1 deliverable from the Gold-Standard plan (Phase 1.5c).  The script:

  1. Validates every ``use-cases/cat-*/uc-*.json`` sidecar against
     ``schemas/uc.schema.json`` using draft-2020-12 JSON Schema.
  2. Reconciles each UC's ``compliance[]`` entry against
     ``data/regulations.json``:
       * the regulation name resolves (directly by shortName, then by
         lowercase alias lookup via ``aliasIndex``);
       * the version exists on that framework;
       * the clause matches the ``clauseGrammar`` of that version;
       * ``assurance_rationale`` is non-empty (schema enforces >=10 chars
         but we restate it for a clearer error path);
       * ``assurance`` is present and valid.
  3. Runs ``tests/golden/compliance-mappings.yaml`` — every hand-curated
     tuple must be present in at least one UC and claim an assurance level
     that is >= the documented minimum.
  4. Computes the three coverage metrics defined in
     ``docs/coverage-methodology.md`` at four scopes (global, per-regulation,
     per-family via the ``derivesFrom`` graph, and per-tier).
  5. Writes a structured JSON report to ``reports/compliance-coverage.json``
     and a human-readable markdown summary to ``docs/compliance-coverage.md``.
  6. Exits with a non-zero status on any validation, reconciliation, or
     golden-test failure so the CI job blocks merges.

Usage:
    python3 scripts/audit_compliance_mappings.py
    python3 scripts/audit_compliance_mappings.py --no-write   # skip report writes
    python3 scripts/audit_compliance_mappings.py --json-only  # suppress pretty output

Design invariants:
    * Deterministic output: every dict/list is sorted before serialisation so
      re-runs on an unchanged catalogue yield byte-identical reports.
    * Zero network access.
    * Only stdlib + ``jsonschema`` + ``pyyaml``; both are installed by the
      ``validate.yml`` workflow and the local ``.venv-feasibility``.

Exit codes:
    0  All checks passed.
    1  One or more checks failed; stderr lists the failures and the
       generated reports include a ``status`` of ``"failed"``.
    2  Uncaught exception (bug).  The stack trace is printed.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError as err:  # pragma: no cover - local ergonomics only
    raise SystemExit(
        "ERROR: jsonschema is required. Install with 'pip install jsonschema'."
    ) from err

try:
    import yaml
except ImportError as err:  # pragma: no cover
    raise SystemExit(
        "ERROR: PyYAML is required. Install with 'pip install PyYAML'."
    ) from err


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "uc.schema.json"
REGS_PATH = REPO_ROOT / "data" / "regulations.json"
GOLDEN_PATH = REPO_ROOT / "tests" / "golden" / "compliance-mappings.yaml"
BASELINE_PATH = REPO_ROOT / "tests" / "golden" / "audit-baseline.json"
UC_GLOB = "use-cases/cat-*/uc-*.json"
REPORT_JSON = REPO_ROOT / "reports" / "compliance-coverage.json"
REPORT_MD = REPO_ROOT / "docs" / "compliance-coverage.md"

# scripts/equipment_lib.py provides the shared EQUIPMENT registry accessor.
# Imported lazily so the audit still runs if the file is missing (CI bootstrap
# safety), but the equipment-orphan lint will be skipped with a "warn" finding.
_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
try:
    from equipment_lib import compile_patterns, match_equipment  # noqa: E402
    _EQUIPMENT_LIB_OK = True
except Exception:  # pragma: no cover - defensive for bootstrap paths
    _EQUIPMENT_LIB_OK = False

# Codes that can be tolerated via the baseline. Adding a code here means CI
# will accept existing occurrences of it but still block new ones.
# ``equipment-orphan`` is baselineable because the lint is informational
# (narrative matches aren't always semantically meaningful — a string like
# "Cisco" may be part of a hostname, not an equipment reference). The
# baseline tracks the current backlog and prevents new regressions without
# blocking on imperfect narrative-to-tag alignment.
BASELINEABLE_CODES = frozenset({"clause-grammar", "equipment-orphan"})


def _deterministic_timestamp() -> str:
    """Return a stable UTC timestamp suitable for committed reports.

    Resolution order (first hit wins):

      1. ``SOURCE_DATE_EPOCH`` environment variable (reproducible-builds
         convention; CI sets this per commit).
      2. The committer date of ``HEAD`` for this repo, via ``git log``.
         Both local runs and CI runs on the same commit therefore produce
         byte-identical reports, so the "generated reports are committed"
         gate only fails when the *structural* contents change.
      3. Current wall-clock UTC time (ultimate fallback).
    """
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    sde = os.environ.get("SOURCE_DATE_EPOCH", "").strip()
    if sde.isdigit():
        return time.strftime(fmt, time.gmtime(int(sde)))
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--pretty=%ct", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        ts = out.stdout.strip()
        if ts.isdigit():
            return time.strftime(fmt, time.gmtime(int(ts)))
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return time.strftime(fmt, time.gmtime())


ASSURANCE_MULTIPLIER = {"full": 1.0, "partial": 0.5, "contributing": 0.25}
ASSURANCE_RANK = {"contributing": 0, "partial": 1, "full": 2}
STATUS_CAP = {
    "verified": 1.0,
    "community": 0.5,
    "__unset__": 0.5,
    "draft": 0.0,
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegVersion:
    """A single version of a regulation framework."""

    framework_id: str
    short_name: str
    tier: int
    version: str
    clause_grammar: re.Pattern
    common_clauses: Tuple[Tuple[str, float], ...]
    authoritative_url: str = ""


@dataclass
class ResolvedRef:
    """Normalised pointer into the regulations catalogue."""

    framework_id: str
    short_name: str
    tier: int
    version: str

    def key(self) -> Tuple[str, str]:
        return (self.framework_id, self.version)


@dataclass
class Finding:
    """A single validation / reconciliation error."""

    level: str  # "error" | "warn" | "baselined"
    uc_id: str
    code: str
    message: str
    path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "uc": self.uc_id,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }

    def fingerprint(self) -> str:
        """Stable identity used for baseline matching.

        Intentionally *excludes* ``level`` so that a finding re-baselined as
        ``"baselined"`` still matches a future occurrence reported as
        ``"error"``.  Any change in any other field is treated as a new,
        distinct finding that the baseline does not cover.
        """
        return f"{self.code}\t{self.uc_id}\t{self.path}\t{self.message}"


@dataclass
class ComplianceEntry:
    """A parsed, reconciled compliance claim on a UC."""

    uc_id: str
    uc_status: str  # draft | community | verified | __unset__
    regulation: str
    version: str
    framework_id: str
    tier: int
    clause: str
    mode: str
    assurance: str
    rationale: str

    @property
    def raw_multiplier(self) -> float:
        return ASSURANCE_MULTIPLIER.get(self.assurance, 0.0)

    @property
    def capped_multiplier(self) -> float:
        cap = STATUS_CAP.get(self.uc_status, 0.0)
        return min(self.raw_multiplier, cap)


@dataclass
class AuditState:
    findings: List[Finding] = field(default_factory=list)
    entries: List[ComplianceEntry] = field(default_factory=list)
    uc_files_checked: int = 0
    uc_files_valid: int = 0
    unknown_regulations: Dict[str, int] = field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _iter_uc_files() -> Iterable[pathlib.Path]:
    for p in sorted(REPO_ROOT.glob(UC_GLOB)):
        if p.is_file():
            yield p


def _validate_uc_schema(
    validator: Draft202012Validator, uc_path: pathlib.Path, state: AuditState
) -> Optional[Dict[str, Any]]:
    try:
        doc = json.loads(uc_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        state.add(
            Finding(
                level="error",
                uc_id=uc_path.stem,
                code="uc-json-parse",
                message=f"invalid JSON: {err}",
                path=str(uc_path.relative_to(REPO_ROOT)),
            )
        )
        return None

    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    for err in errors:
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        state.add(
            Finding(
                level="error",
                uc_id=str(doc.get("id", uc_path.stem)),
                code="uc-schema-validation",
                message=err.message,
                path=f"{uc_path.relative_to(REPO_ROOT)}:{path}",
            )
        )
    if errors:
        return None
    return doc


# ---------------------------------------------------------------------------
# Regulations catalogue
# ---------------------------------------------------------------------------


class RegulationsCatalogue:
    """In-memory index over ``data/regulations.json``."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self._raw = raw
        self._versions_by_key: Dict[Tuple[str, str], RegVersion] = {}
        self._by_short_name: Dict[str, Dict[str, RegVersion]] = {}
        self._by_framework_id: Dict[str, Dict[str, RegVersion]] = {}
        self._alias_index: Dict[str, str] = {}
        self._framework_meta: Dict[str, Dict[str, Any]] = {}
        self._derives_from: Dict[str, Dict[str, Any]] = {}
        self._build()

    @classmethod
    def load(cls, path: pathlib.Path = REGS_PATH) -> "RegulationsCatalogue":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def _build(self) -> None:
        for framework in self._raw.get("frameworks", []):
            fid = framework["id"]
            short = framework.get("shortName", "")
            tier = int(framework.get("tier", 3))
            self._framework_meta[fid] = {
                "name": framework.get("name", ""),
                "shortName": short,
                "tier": tier,
                "jurisdiction": framework.get("jurisdiction", []),
                "tags": framework.get("tags", []),
                "aliases": framework.get("aliases", []),
            }
            # Aliases (including shortName & id) all resolve to the framework id.
            for alias in list(framework.get("aliases", [])) + [short, fid, framework.get("name", "")]:
                if not alias:
                    continue
                self._alias_index[alias.strip().lower()] = fid
            for ver in framework.get("versions", []):
                version = ver["version"]
                grammar = re.compile(ver["clauseGrammar"])
                common = tuple(
                    (c["clause"], float(c.get("priorityWeight", 0.0)))
                    for c in ver.get("commonClauses", [])
                )
                rv = RegVersion(
                    framework_id=fid,
                    short_name=short,
                    tier=tier,
                    version=version,
                    clause_grammar=grammar,
                    common_clauses=common,
                    authoritative_url=ver.get("authoritativeUrl", ""),
                )
                self._versions_by_key[(fid, version)] = rv
                self._by_short_name.setdefault(short, {})[version] = rv
                self._by_framework_id.setdefault(fid, {})[version] = rv

        for alias, fid in self._raw.get("aliasIndex", {}).items():
            if alias.startswith("$"):
                continue
            self._alias_index[alias.strip().lower()] = fid
        self._derives_from = self._raw.get("derivesFrom", {})

    # ------- lookups -------

    def resolve_framework(self, name: str) -> Optional[str]:
        """Return canonical framework_id for a UC-supplied regulation string."""

        key = (name or "").strip().lower()
        if not key:
            return None
        return self._alias_index.get(key)

    def get_version(self, framework_id: str, version: str) -> Optional[RegVersion]:
        return self._versions_by_key.get((framework_id, version))

    def framework_meta(self, framework_id: str) -> Dict[str, Any]:
        return self._framework_meta.get(framework_id, {})

    def versions_for_framework(self, framework_id: str) -> Dict[str, RegVersion]:
        return self._by_framework_id.get(framework_id, {})

    def all_framework_ids(self) -> List[str]:
        return sorted(self._by_framework_id.keys())

    def derives_from(self) -> Dict[str, Dict[str, Any]]:
        return self._derives_from

    def family_for(self, framework_id: str) -> str:
        """Return a family identifier.

        The family is the root of the derivesFrom chain; non-derivative
        frameworks are their own family.
        """

        current = framework_id
        visited = set()
        while current in self._derives_from and current not in visited:
            visited.add(current)
            parent = self._derives_from[current].get("parent")
            if not parent or parent == current:
                break
            current = parent
        return current


# ---------------------------------------------------------------------------
# Compliance reconciliation
# ---------------------------------------------------------------------------


def _uc_status(doc: Mapping[str, Any]) -> str:
    return doc.get("status") or "__unset__"


def _reconcile_compliance(doc: Mapping[str, Any], regs: RegulationsCatalogue, state: AuditState) -> None:
    uc_id = str(doc.get("id", ""))
    status = _uc_status(doc)
    for idx, entry in enumerate(doc.get("compliance", []) or []):
        reg_name = entry.get("regulation", "")
        version = entry.get("version", "")
        clause = entry.get("clause", "")
        mode = entry.get("mode", "")
        assurance = entry.get("assurance", "")
        rationale = entry.get("assurance_rationale", "")

        path = f"compliance[{idx}]"
        fid = regs.resolve_framework(reg_name)
        if not fid:
            state.unknown_regulations[reg_name] = state.unknown_regulations.get(reg_name, 0) + 1
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="unknown-regulation",
                    message=f"regulation '{reg_name}' not found in data/regulations.json (aliasIndex / shortName)",
                    path=path,
                )
            )
            continue

        rv = regs.get_version(fid, version)
        if not rv:
            known = sorted(regs.versions_for_framework(fid).keys())
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="unknown-version",
                    message=(
                        f"regulation '{reg_name}' (id={fid}) has no version '{version}'. "
                        f"Known versions: {known}"
                    ),
                    path=path,
                )
            )
            continue

        if not rv.clause_grammar.match(clause or ""):
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="clause-grammar",
                    message=(
                        f"clause '{clause}' does not match clauseGrammar "
                        f"/{rv.clause_grammar.pattern}/ for {rv.short_name}@{rv.version}"
                    ),
                    path=path,
                )
            )
            continue

        if assurance not in ASSURANCE_MULTIPLIER:
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="assurance-invalid",
                    message=(
                        f"assurance '{assurance}' not in {sorted(ASSURANCE_MULTIPLIER)}"
                    ),
                    path=path,
                )
            )
            continue

        if not rationale or len(rationale.strip()) < 10:
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="assurance-rationale-missing",
                    message=(
                        "assurance_rationale is required and must be at least "
                        "10 characters; reviewers need the explicit judgement"
                    ),
                    path=path,
                )
            )
            continue

        if mode not in {"satisfies", "detects-violation-of"}:
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="mode-invalid",
                    message=f"mode '{mode}' must be 'satisfies' or 'detects-violation-of'",
                    path=path,
                )
            )
            continue

        state.entries.append(
            ComplianceEntry(
                uc_id=uc_id,
                uc_status=status,
                regulation=rv.short_name,
                version=version,
                framework_id=fid,
                tier=rv.tier,
                clause=clause,
                mode=mode,
                assurance=assurance,
                rationale=rationale.strip(),
            )
        )


# ---------------------------------------------------------------------------
# Equipment-orphan lint (informational, cat-22 regulatory UCs)
# ---------------------------------------------------------------------------


_EQUIPMENT_PATTERNS_CACHE: Optional[list] = None


def _equipment_patterns() -> list:
    """Lazy-load the EQUIPMENT pattern list once per audit run."""
    global _EQUIPMENT_PATTERNS_CACHE
    if _EQUIPMENT_PATTERNS_CACHE is None and _EQUIPMENT_LIB_OK:
        _EQUIPMENT_PATTERNS_CACHE = compile_patterns()
    return _EQUIPMENT_PATTERNS_CACHE or []


def _lint_equipment_orphans(doc: Mapping[str, Any], state: AuditState) -> None:
    """Flag UCs whose narrative mentions equipment that's not in ``equipment[]``.

    Intent: close the cat-22 audit-evidence gap described in
    ``docs/equipment-table.md``. When a regulatory UC's SPL, description,
    or implementation text mentions (for example) "Palo Alto GlobalProtect"
    but the structured ``equipment[]`` field doesn't contain ``paloalto``,
    an auditor filtering the UI by "Palo Alto" won't see this UC. The
    generator in ``scripts/generate_equipment_tags.py`` should have caught
    it; this lint is the belt-and-suspenders check.

    The lint only runs on cat-22 UCs because:
    1. Today cat-22 is the only category with sidecars that have the
       structured ``equipment[]`` field.
    2. It is the category that auditors, regulators, and DPOs directly
       query. False-negatives here have compliance consequences.

    Findings are emitted at ``warn`` level (non-blocking) to give
    maintainers signal without creating a hard CI gate that would block
    on imperfect narrative-to-tag alignment (e.g. hostnames or vendor
    mentions that are not meant as equipment claims). The
    ``equipment-orphan`` code is in ``BASELINEABLE_CODES`` so the
    existing backlog can be captured in the baseline and new
    regressions will be detected automatically.
    """
    if not _EQUIPMENT_LIB_OK:
        return
    uc_id = str(doc.get("id", ""))
    if not uc_id.startswith("22."):
        return

    patterns = _equipment_patterns()
    if not patterns:
        return

    tagged_eq = {str(e).lower() for e in (doc.get("equipment") or []) if isinstance(e, str)}
    tagged_models = {str(m).lower() for m in (doc.get("equipmentModels") or []) if isinstance(m, str)}

    # Build the narrative text the same way the generator does so the two
    # agree on what "mentioned in the narrative" means. See
    # scripts/generate_equipment_tags.py::_collect_narrative_text().
    parts: List[str] = []
    for key in ("description", "implementation", "spl", "dataSources"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
        elif isinstance(val, list):
            parts.extend(str(v) for v in val if isinstance(v, (str, int, float)))
    app_field = doc.get("app")
    if isinstance(app_field, str) and app_field.strip():
        parts.append(app_field)
    elif isinstance(app_field, list):
        parts.extend(str(v) for v in app_field if isinstance(v, (str, int, float)))
    narrative = "\n".join(parts)
    if not narrative:
        return

    found_eq, found_models = match_equipment(narrative, patterns, min_pattern_len=4)
    missing_eq = sorted(eq for eq in found_eq if eq.lower() not in tagged_eq)
    missing_models = sorted(m for m in found_models if m.lower() not in tagged_models)

    if not missing_eq and not missing_models:
        return

    parts_msg: List[str] = []
    if missing_eq:
        parts_msg.append(f"equipment {missing_eq}")
    if missing_models:
        parts_msg.append(f"equipmentModels {missing_models}")
    detail = " and ".join(parts_msg)
    state.add(
        Finding(
            level="warn",
            uc_id=uc_id,
            code="equipment-orphan",
            message=(
                f"narrative text references {detail} that is not present in "
                "the structured equipment[] / equipmentModels[] fields; "
                "auditors filtering by this equipment in the UI will miss "
                "this UC. Regenerate with "
                "scripts/generate_equipment_tags.py or add the tags "
                "manually if the match is a semantic false positive."
            ),
            path="equipment",
        )
    )


# ---------------------------------------------------------------------------
# Golden tuple gate
# ---------------------------------------------------------------------------


def _run_golden_tests(entries: Sequence[ComplianceEntry], state: AuditState) -> Dict[str, Any]:
    if not GOLDEN_PATH.exists():
        state.add(
            Finding(
                level="error",
                uc_id="<golden>",
                code="golden-missing",
                message=f"golden test file missing: {GOLDEN_PATH.relative_to(REPO_ROOT)}",
            )
        )
        return {"total": 0, "passed": 0, "failed": 0, "failures": []}

    golden = yaml.safe_load(GOLDEN_PATH.read_text(encoding="utf-8")) or {}
    tuples = golden.get("tuples", [])
    if not isinstance(tuples, list) or not tuples:
        state.add(
            Finding(
                level="error",
                uc_id="<golden>",
                code="golden-empty",
                message="tests/golden/compliance-mappings.yaml has no tuples",
            )
        )
        return {"total": 0, "passed": 0, "failed": 0, "failures": []}

    # Index live entries.
    by_key: Dict[Tuple[str, str, str, str, str], List[ComplianceEntry]] = defaultdict(list)
    for e in entries:
        by_key[(e.uc_id, e.regulation, e.version, e.clause, e.mode)].append(e)

    failures: List[Dict[str, Any]] = []
    passed = 0
    for t in tuples:
        uc_id = str(t.get("uc", ""))
        reg = str(t.get("regulation", ""))
        version = str(t.get("version", ""))
        clause = str(t.get("clause", ""))
        mode = str(t.get("mode", ""))
        min_a = str(t.get("min_assurance", "contributing"))

        matches = by_key.get((uc_id, reg, version, clause, mode), [])
        if not matches:
            failures.append(
                {
                    "uc": uc_id,
                    "regulation": reg,
                    "version": version,
                    "clause": clause,
                    "mode": mode,
                    "reason": "tuple-not-found",
                }
            )
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="golden-missing-tuple",
                    message=f"golden tuple missing: {reg}@{version} clause {clause} mode {mode}",
                )
            )
            continue

        best = max((ASSURANCE_RANK.get(m.assurance, -1) for m in matches), default=-1)
        min_rank = ASSURANCE_RANK.get(min_a, 0)
        if best < min_rank:
            failures.append(
                {
                    "uc": uc_id,
                    "regulation": reg,
                    "version": version,
                    "clause": clause,
                    "mode": mode,
                    "reason": "assurance-below-min",
                    "min_assurance": min_a,
                }
            )
            state.add(
                Finding(
                    level="error",
                    uc_id=uc_id,
                    code="golden-assurance-below-min",
                    message=(
                        f"assurance below min for {reg}@{version} {clause}: "
                        f"expected >= {min_a}"
                    ),
                )
            )
        else:
            passed += 1
    return {
        "total": len(tuples),
        "passed": passed,
        "failed": len(failures),
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Coverage metrics
# ---------------------------------------------------------------------------


@dataclass
class Metrics:
    denominator_count: int
    denominator_weighted: float
    clause_pct: float
    priority_pct: float
    assurance_pct: float
    clauses_covered: int
    weighted_covered: float
    assurance_numerator: float


def _metrics_for(
    common_clauses: Sequence[Tuple[str, float]],
    coverage: Mapping[str, float],  # clause -> max capped multiplier
) -> Metrics:
    denom_count = len(common_clauses)
    denom_weight = sum(w for _c, w in common_clauses) or 0.0
    clauses_covered = 0
    weighted_covered = 0.0
    assurance_num = 0.0
    for clause, weight in common_clauses:
        if clause in coverage:
            clauses_covered += 1
            weighted_covered += weight
            assurance_num += weight * coverage[clause]
    if denom_count == 0:
        return Metrics(0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0)
    clause_pct = (clauses_covered / denom_count) * 100.0
    priority_pct = (weighted_covered / denom_weight) * 100.0 if denom_weight else 0.0
    assurance_pct = (assurance_num / denom_weight) * 100.0 if denom_weight else 0.0
    return Metrics(
        denominator_count=denom_count,
        denominator_weighted=denom_weight,
        clause_pct=round(clause_pct, 4),
        priority_pct=round(priority_pct, 4),
        assurance_pct=round(assurance_pct, 4),
        clauses_covered=clauses_covered,
        weighted_covered=round(weighted_covered, 4),
        assurance_numerator=round(assurance_num, 4),
    )


def _build_coverage_by_version(
    entries: Sequence[ComplianceEntry],
) -> Dict[Tuple[str, str], Dict[str, float]]:
    """Return (framework_id, version) -> {clause: max capped multiplier}.

    Only non-draft UCs count (STATUS_CAP excludes draft via multiplier=0).
    The multiplier is the status-capped value from
    ``ComplianceEntry.capped_multiplier``.
    """

    cov: Dict[Tuple[str, str], Dict[str, float]] = defaultdict(dict)
    for e in entries:
        cap = e.capped_multiplier
        if cap <= 0.0:
            continue
        key = (e.framework_id, e.version)
        current = cov[key].get(e.clause, 0.0)
        if cap > current:
            cov[key][e.clause] = cap
    return cov


def _compute_coverage(
    entries: Sequence[ComplianceEntry], regs: RegulationsCatalogue
) -> Dict[str, Any]:
    cov_by_version = _build_coverage_by_version(entries)

    per_version: Dict[str, Metrics] = {}
    per_version_tier: Dict[str, int] = {}
    per_family: Dict[str, List[Metrics]] = defaultdict(list)

    agg_denom_ct = 0
    agg_denom_w = 0.0
    agg_covered_ct = 0
    agg_covered_w = 0.0
    agg_assurance = 0.0

    tier_totals: Dict[int, Dict[str, float]] = defaultdict(
        lambda: {"dc": 0, "dw": 0.0, "cc": 0, "cw": 0.0, "an": 0.0}
    )

    for fid in regs.all_framework_ids():
        meta = regs.framework_meta(fid)
        tier = int(meta.get("tier", 3))
        family = regs.family_for(fid)
        for version, rv in regs.versions_for_framework(fid).items():
            key = (fid, version)
            cov = cov_by_version.get(key, {})
            m = _metrics_for(rv.common_clauses, cov)
            label = f"{meta.get('shortName', fid)}@{version}"
            per_version[label] = m
            per_version_tier[label] = tier
            per_family[family].append(m)

            agg_denom_ct += m.denominator_count
            agg_denom_w += m.denominator_weighted
            agg_covered_ct += m.clauses_covered
            agg_covered_w += m.weighted_covered
            agg_assurance += m.assurance_numerator

            tt = tier_totals[tier]
            tt["dc"] += m.denominator_count
            tt["dw"] += m.denominator_weighted
            tt["cc"] += m.clauses_covered
            tt["cw"] += m.weighted_covered
            tt["an"] += m.assurance_numerator

    def _finalise(dc: float, dw: float, cc: float, cw: float, an: float) -> Dict[str, float]:
        if not dc:
            return {"clause_pct": 0.0, "priority_pct": 0.0, "assurance_pct": 0.0,
                    "denominator_count": 0, "denominator_weighted": 0.0,
                    "clauses_covered": 0, "weighted_covered": 0.0,
                    "assurance_numerator": 0.0}
        return {
            "clause_pct": round((cc / dc) * 100.0, 4) if dc else 0.0,
            "priority_pct": round((cw / dw) * 100.0, 4) if dw else 0.0,
            "assurance_pct": round((an / dw) * 100.0, 4) if dw else 0.0,
            "denominator_count": int(dc),
            "denominator_weighted": round(dw, 4),
            "clauses_covered": int(cc),
            "weighted_covered": round(cw, 4),
            "assurance_numerator": round(an, 4),
        }

    global_metrics = _finalise(
        agg_denom_ct, agg_denom_w, agg_covered_ct, agg_covered_w, agg_assurance
    )

    per_tier: Dict[str, Dict[str, float]] = {}
    for tier in sorted(tier_totals.keys()):
        t = tier_totals[tier]
        per_tier[f"tier-{tier}"] = _finalise(t["dc"], t["dw"], t["cc"], t["cw"], t["an"])

    per_family_final: Dict[str, Dict[str, float]] = {}
    for family, ms in per_family.items():
        dc = sum(m.denominator_count for m in ms)
        dw = sum(m.denominator_weighted for m in ms)
        cc = sum(m.clauses_covered for m in ms)
        cw = sum(m.weighted_covered for m in ms)
        an = sum(m.assurance_numerator for m in ms)
        per_family_final[family] = _finalise(dc, dw, cc, cw, an)

    per_version_final: Dict[str, Dict[str, Any]] = {}
    for label, m in per_version.items():
        d = _finalise(
            m.denominator_count,
            m.denominator_weighted,
            m.clauses_covered,
            m.weighted_covered,
            m.assurance_numerator,
        )
        d["tier"] = per_version_tier[label]
        per_version_final[label] = d

    return {
        "global": global_metrics,
        "perTier": per_tier,
        "perFamily": dict(sorted(per_family_final.items())),
        "perVersion": dict(sorted(per_version_final.items())),
    }


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def _write_json_report(payload: Dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _markdown_for(payload: Dict[str, Any]) -> str:
    g = payload["coverage"]["global"]
    out: List[str] = []
    out.append("# Compliance coverage report")
    out.append("")
    out.append(
        f"Status: **{payload['status']}**  |  Generated: {payload['generatedAt']}"
    )
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(f"* UC files checked: **{payload['counts']['ucFilesChecked']}**")
    out.append(f"* UC files valid:   **{payload['counts']['ucFilesValid']}**")
    out.append(
        f"* Compliance entries: **{payload['counts']['complianceEntries']}**"
    )
    out.append(
        f"* Findings: **{payload['counts']['findings']}** "
        f"(errors: **{payload['counts']['errors']}**, "
        f"baselined: **{payload['counts']['baselined']}**)"
    )
    baseline = payload.get("baseline", {})
    if baseline.get("enabled"):
        out.append(
            f"* Baseline (`{baseline['path']}`): total **{baseline.get('total', 0)}**, "
            f"tolerated this run **{baseline.get('matched', 0)}**, "
            f"new errors **{baseline.get('newErrors', 0)}**, "
            f"unused fingerprints **{len(baseline.get('unused', []))}** "
            f"(see `docs/coverage-methodology.md` § 12)"
        )
    out.append("")
    out.append("## Global coverage (all tiers)")
    out.append("")
    out.append(f"* Clause coverage %: **{g['clause_pct']}**")
    out.append(f"* Priority-weighted %: **{g['priority_pct']}**")
    out.append(f"* Assurance-adjusted %: **{g['assurance_pct']}**")
    out.append("")
    out.append("## Per tier")
    out.append("")
    out.append("| Tier | Clause % | Priority-weighted % | Assurance-adjusted % |")
    out.append("|------|----------|----------------------|-----------------------|")
    for tier, m in payload["coverage"]["perTier"].items():
        out.append(
            f"| {tier} | {m['clause_pct']} | {m['priority_pct']} | {m['assurance_pct']} |"
        )
    out.append("")
    out.append("## Per family (derivesFrom roots)")
    out.append("")
    out.append("| Family root | Clause % | Priority-weighted % | Assurance-adjusted % |")
    out.append("|-------------|----------|----------------------|-----------------------|")
    for family, m in payload["coverage"]["perFamily"].items():
        out.append(
            f"| {family} | {m['clause_pct']} | {m['priority_pct']} | {m['assurance_pct']} |"
        )
    out.append("")
    out.append("## Per regulation-version")
    out.append("")
    out.append("| Regulation@Version | Tier | Clause % | Priority-weighted % | Assurance-adjusted % |")
    out.append("|---------------------|------|----------|----------------------|-----------------------|")
    for label, m in payload["coverage"]["perVersion"].items():
        out.append(
            f"| {label} | {m['tier']} | {m['clause_pct']} | {m['priority_pct']} | {m['assurance_pct']} |"
        )
    out.append("")
    out.append("## Golden tuples")
    out.append("")
    golden = payload["golden"]
    out.append(
        f"* Total: **{golden['total']}**  |  Passed: **{golden['passed']}**  |  "
        f"Failed: **{golden['failed']}**"
    )
    out.append("")
    # Blocking findings first, then a compact view of the baseline tail so the
    # markdown doubles as a cleanup worklist for Phase 3.1.
    blocking = [f for f in payload["findings"] if f["level"] == "error"]
    baselined = [f for f in payload["findings"] if f["level"] == "baselined"]
    if blocking:
        out.append("## Blocking findings")
        out.append("")
        out.append("| Level | UC | Code | Path | Message |")
        out.append("|-------|----|------|------|---------|")
        for f in blocking[:50]:
            msg = str(f.get("message", "")).replace("|", "\\|")
            out.append(
                f"| {f['level']} | {f['uc']} | {f['code']} | {f.get('path','')} | {msg} |"
            )
        if len(blocking) > 50:
            out.append(f"")
            out.append(f"_… and {len(blocking) - 50} more blocking findings. See `reports/compliance-coverage.json`._")
        out.append("")
    if baselined:
        out.append("## Baselined (tolerated) findings — Phase 3.1 worklist (first 20)")
        out.append("")
        out.append(
            "_These are pre-existing `clause-grammar` issues carried by "
            "`tests/golden/audit-baseline.json`; they do not block CI but "
            "should be resolved incrementally. The full list is in the JSON report._"
        )
        out.append("")
        out.append("| UC | Code | Path | Message |")
        out.append("|----|------|------|---------|")
        for f in baselined[:20]:
            msg = str(f.get("message", "")).replace("|", "\\|")
            out.append(
                f"| {f['uc']} | {f['code']} | {f.get('path','')} | {msg} |"
            )
        if len(baselined) > 20:
            out.append(f"")
            out.append(
                f"_… and {len(baselined) - 20} more baselined findings. "
                f"See `reports/compliance-coverage.json`._"
            )
        out.append("")
    out.append("---")
    out.append("")
    out.append(
        "_This file is generated by `scripts/audit_compliance_mappings.py`. "
        "See `docs/coverage-methodology.md` for the formal definitions._"
    )
    return "\n".join(out) + "\n"


def _write_markdown_report(payload: Dict[str, Any]) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(_markdown_for(payload), encoding="utf-8")


# ---------------------------------------------------------------------------
# Baseline mechanism
# ---------------------------------------------------------------------------


def _load_baseline(path: pathlib.Path) -> Dict[str, Any]:
    """Load the committed baseline file.

    Returns an empty baseline skeleton if the file is missing so first-time
    runs still work.  The structure is deliberately small so diffs are
    readable: ``{ "version": 1, "generatedAt": "...", "fingerprints": [...] }``.
    """
    if not path.exists():
        return {"version": 1, "generatedAt": "", "fingerprints": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise SystemExit(
            f"ERROR: {path.relative_to(REPO_ROOT)} is not valid JSON: {err}"
        ) from err
    if not isinstance(data, dict) or "fingerprints" not in data:
        raise SystemExit(
            f"ERROR: {path.relative_to(REPO_ROOT)} is malformed "
            "(expected {{'version': 1, 'fingerprints': [...]}})."
        )
    return data


def _apply_baseline(findings: List[Finding], baseline_fps: set[str]) -> Tuple[int, int, int]:
    """Downgrade matching findings to level ``baselined`` in place.

    Only codes in ``BASELINEABLE_CODES`` may be tolerated; anything else
    (schema errors, golden-test failures, unknown regulations) continues
    to block regardless of the baseline.

    Returns ``(blocking_errors, baselined_count, new_errors)``:
      * ``blocking_errors`` — findings that still count as errors after
        baseline is applied (legitimately new or structurally non-ignorable).
      * ``baselined_count`` — findings matched by a baseline fingerprint.
      * ``new_errors`` — baselineable findings with no matching fingerprint.
    """
    blocking = 0
    baselined = 0
    new_errors = 0
    for f in findings:
        if f.level != "error":
            continue
        if f.code not in BASELINEABLE_CODES:
            blocking += 1
            continue
        if f.fingerprint() in baseline_fps:
            f.level = "baselined"
            baselined += 1
            continue
        blocking += 1
        new_errors += 1
    return blocking, baselined, new_errors


def _write_baseline(path: pathlib.Path, findings: List[Finding]) -> int:
    """(Re)write the baseline file from the current set of baselineable errors.

    Called with ``--update-baseline``.  Deterministic: fingerprints are
    sorted so diffs stay minimal.  Non-baselineable errors are never
    written (they must be fixed, not tolerated).
    """
    eligible = [
        f
        for f in findings
        if f.level in ("error", "baselined") and f.code in BASELINEABLE_CODES
    ]
    fps = sorted({f.fingerprint() for f in eligible})
    payload = {
        "version": 1,
        "generatedAt": _deterministic_timestamp(),
        "description": (
            "Known, tolerated audit findings. Regenerate with "
            "`python scripts/audit_compliance_mappings.py --update-baseline`. "
            "Shrink over time: Phase 3.1 targets a zero-baseline state for "
            "tier-1 regulations before release 4.0."
        ),
        "count": len(fps),
        "fingerprints": fps,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return len(fps)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate UC sidecars, reconcile compliance[] entries against "
            "the regulations catalogue, run the golden tuple gate, and "
            "compute the three coverage metrics."
        )
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing reports/compliance-coverage.json and docs/compliance-coverage.md.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Suppress pretty stdout output; keep only the machine-readable JSON line.",
    )
    parser.add_argument(
        "--baseline",
        default=str(BASELINE_PATH.relative_to(REPO_ROOT)),
        help=(
            "Path to the baseline JSON file used to tolerate known "
            "findings (default: tests/golden/audit-baseline.json). "
            "Only codes in BASELINEABLE_CODES can ever be baselined."
        ),
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Ignore the baseline file entirely; treat every finding as blocking.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help=(
            "Rewrite the baseline file from the current set of findings. "
            "Use sparingly: the goal is to SHRINK the baseline over time, "
            "not to paper over new issues."
        ),
    )
    args = parser.parse_args()

    state = AuditState()

    schema = _load_schema()
    validator = Draft202012Validator(schema)
    regs = RegulationsCatalogue.load()

    for uc_path in _iter_uc_files():
        state.uc_files_checked += 1
        doc = _validate_uc_schema(validator, uc_path, state)
        if doc is None:
            continue
        state.uc_files_valid += 1
        _reconcile_compliance(doc, regs, state)
        _lint_equipment_orphans(doc, state)

    golden = _run_golden_tests(state.entries, state)
    coverage = _compute_coverage(state.entries, regs)

    baseline_path = (REPO_ROOT / args.baseline).resolve()
    baseline_fps: set[str] = set()
    baseline_meta: Dict[str, Any] = {"enabled": False, "path": str(baseline_path.relative_to(REPO_ROOT)), "matched": 0, "newErrors": 0, "unused": []}
    if not args.no_baseline and not args.update_baseline:
        baseline_data = _load_baseline(baseline_path)
        baseline_fps = set(baseline_data.get("fingerprints", []))
        blocking, matched, new_errors = _apply_baseline(state.findings, baseline_fps)
        # Track fingerprints present in the baseline but not observed this run;
        # these should eventually be pruned by a later --update-baseline commit.
        observed = {f.fingerprint() for f in state.findings if f.level == "baselined"}
        unused = sorted(baseline_fps - observed)
        baseline_meta = {
            "enabled": True,
            "path": str(baseline_path.relative_to(REPO_ROOT)),
            "total": len(baseline_fps),
            "matched": matched,
            "newErrors": new_errors,
            "unused": unused,
        }
        error_count = blocking
    else:
        error_count = sum(1 for f in state.findings if f.level == "error")

    status = "passed" if error_count == 0 else "failed"

    payload: Dict[str, Any] = {
        "status": status,
        "generatedAt": _deterministic_timestamp(),
        "schemaVersion": schema.get("schemaVersion"),
        "regulationsVersion": regs._raw.get("schemaVersion"),
        "counts": {
            "ucFilesChecked": state.uc_files_checked,
            "ucFilesValid": state.uc_files_valid,
            "complianceEntries": len(state.entries),
            "findings": len(state.findings),
            "errors": error_count,
            "baselined": sum(1 for f in state.findings if f.level == "baselined"),
            "unknownRegulations": state.unknown_regulations,
        },
        "baseline": baseline_meta,
        "golden": golden,
        "coverage": coverage,
        "findings": [f.to_dict() for f in state.findings],
    }

    if args.update_baseline:
        written = _write_baseline(baseline_path, state.findings)
        sys.stderr.write(
            f"Wrote baseline to {baseline_path.relative_to(REPO_ROOT)} "
            f"with {written} fingerprint(s).\n"
        )
        # After regenerating the baseline the *next* run should be clean;
        # return success so CI doesn't block on this one-shot rewrite.
        return 0

    if not args.no_write:
        _write_json_report(payload)
        _write_markdown_report(payload)

    if args.json_only:
        json.dump({"status": status, "errors": error_count}, sys.stdout)
        sys.stdout.write("\n")
    else:
        _print_pretty(payload)

    return 0 if status == "passed" else 1


def _print_pretty(payload: Dict[str, Any]) -> None:
    out = sys.stdout
    out.write(
        f"Compliance audit: {payload['status'].upper()}  "
        f"(UC files valid={payload['counts']['ucFilesValid']}/"
        f"{payload['counts']['ucFilesChecked']}, "
        f"entries={payload['counts']['complianceEntries']}, "
        f"errors={payload['counts']['errors']}, "
        f"baselined={payload['counts']['baselined']})\n"
    )
    g = payload["coverage"]["global"]
    out.write(
        f"  Global   clause% {g['clause_pct']:>6.2f}  "
        f"priority% {g['priority_pct']:>6.2f}  "
        f"assurance% {g['assurance_pct']:>6.2f}\n"
    )
    for tier, m in payload["coverage"]["perTier"].items():
        out.write(
            f"  {tier:<8s} clause% {m['clause_pct']:>6.2f}  "
            f"priority% {m['priority_pct']:>6.2f}  "
            f"assurance% {m['assurance_pct']:>6.2f}\n"
        )
    golden = payload["golden"]
    out.write(
        f"  Golden   total={golden['total']} passed={golden['passed']} "
        f"failed={golden['failed']}\n"
    )
    baseline = payload.get("baseline", {})
    if baseline.get("enabled"):
        out.write(
            f"  Baseline {baseline['path']}: "
            f"tolerated={baseline.get('matched', 0)}, "
            f"new-errors={baseline.get('newErrors', 0)}, "
            f"unused={len(baseline.get('unused', []))}\n"
        )
    blocking = [f for f in payload["findings"] if f["level"] == "error"]
    if blocking:
        out.write("\nBlocking findings (first 20):\n")
        for f in blocking[:20]:
            out.write(f"  [{f['level']}] {f['uc']:<10s} {f['code']:<30s} {f['message']}\n")
        remaining = len(blocking) - 20
        if remaining > 0:
            out.write(f"  ... and {remaining} more. See reports/compliance-coverage.json\n")


if __name__ == "__main__":  # pragma: no cover
    try:
        sys.exit(main())
    except Exception:  # pragma: no cover
        import traceback

        traceback.print_exc()
        sys.exit(2)
