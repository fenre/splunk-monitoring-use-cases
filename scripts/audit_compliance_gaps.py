#!/usr/bin/env python3
"""Per-regulation clause-level gap analysis.

Phase 2.1 deliverable of the gold-standard plan.  While
``scripts/audit_compliance_mappings.py`` produces aggregate coverage
percentages, auditors need a **clause-by-clause** view that answers

    "For regulation X version Y, which ``commonClauses[]`` entries have
     at least one UC tagging them, and which are still gaps?"

This script walks the same inputs as the coverage audit and emits

* ``reports/compliance-gaps.json`` — the canonical machine-readable report
  (deterministic, sorted keys, 2-space indent).
* ``docs/compliance-gaps.md`` — human-readable summary with per-framework
  tables and a priority-ranked "next clauses to cover" worklist for every
  tier-1 framework.

Design invariants
-----------------

* **Deterministic.** The same inputs always yield byte-identical output;
  CI runs ``--check`` to diff the committed report against a fresh run.
* **Offline.** No network calls; reads are confined to the repo.
* **Compatible alias resolution.** Uses the same lower-case alias lookup
  (shortName → framework id + ``aliasIndex``) that
  ``scripts/audit_compliance_mappings.py`` uses, so a regulation that
  resolves there also resolves here.
* **Status-aware.** Draft UCs count toward coverage with a zero multiplier
  (matching the coverage methodology) so they are listed in ``uc_ids``
  but do **not** flip a clause from "gap" to "covered".

CLI
---

    # Regenerate both artefacts in place
    python3 scripts/audit_compliance_gaps.py

    # Determinism guard (CI)
    python3 scripts/audit_compliance_gaps.py --check

    # Only tier-1 frameworks (the primary focus of Phase 2.1)
    python3 scripts/audit_compliance_gaps.py --tier 1

Exit codes
----------
    0  Success (or --check found no drift).
    1  Drift detected (--check) or regulations.json failed to load.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile
import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REGS_PATH = REPO_ROOT / "data" / "regulations.json"
USE_CASES_DIR = REPO_ROOT / "use-cases"
REPORT_JSON = REPO_ROOT / "reports" / "compliance-gaps.json"
REPORT_MD = REPO_ROOT / "docs" / "compliance-gaps.md"

# Status → coverage multiplier, mirrors docs/coverage-methodology.md §8.
# Draft UCs still appear in uc_ids[] but do not flip coverage state.
STATUS_MULTIPLIER: Dict[str, float] = {
    "production": 1.0,
    "stable": 1.0,
    "active": 1.0,
    "review": 0.75,
    "beta": 0.75,
    "draft": 0.0,
    "experimental": 0.0,
    "deprecated": 0.0,
    "archived": 0.0,
    "__unset__": 1.0,  # Missing status defaults to production.
}

# Assurance ranking used to pick the "best" assurance for a clause when
# multiple UCs tag it.  Vocabulary mirrors ``schemas/uc.schema.json`` which
# restricts ``assurance`` to ``{full, partial, contributing}``; higher rank
# means a stronger audit claim (full > partial > contributing).
ASSURANCE_RANK: Dict[str, int] = {
    "full": 3,
    "partial": 2,
    "contributing": 1,
}

# Sample cap for uc_ids[] in the machine-readable report.  Stops the
# worklist from ballooning for well-covered clauses.
UC_SAMPLE_LIMIT = 8


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClauseEntry:
    clause: str
    topic: str
    priority_weight: float


@dataclass(frozen=True)
class RegVersion:
    framework_id: str
    short_name: str
    name: str
    tier: int
    version: str
    authoritative_url: str
    clauses: Tuple[ClauseEntry, ...]


@dataclass
class UcComplianceHit:
    uc_id: str
    status: str
    assurance: str
    mode: str

    @property
    def multiplier(self) -> float:
        return STATUS_MULTIPLIER.get((self.status or "__unset__").lower(), 1.0)


@dataclass
class ClauseGap:
    clause: str
    topic: str
    priority_weight: float
    uc_ids: List[str] = field(default_factory=list)
    draft_uc_ids: List[str] = field(default_factory=list)
    max_assurance: Optional[str] = None

    @property
    def uc_count(self) -> int:
        return len(self.uc_ids)

    @property
    def draft_count(self) -> int:
        return len(self.draft_uc_ids)

    @property
    def covered(self) -> bool:
        return self.uc_count > 0

    def to_json(self) -> Dict[str, Any]:
        sample = sorted(self.uc_ids)[:UC_SAMPLE_LIMIT]
        drafts = sorted(self.draft_uc_ids)[:UC_SAMPLE_LIMIT]
        return {
            "clause": self.clause,
            "covered": self.covered,
            "draft_uc_count": self.draft_count,
            "draft_uc_ids": drafts,
            "max_assurance": self.max_assurance,
            "priority_weight": round(self.priority_weight, 4),
            "topic": self.topic,
            "uc_count": self.uc_count,
            "uc_ids": sample,
        }


# ---------------------------------------------------------------------------
# Regulations catalogue (lightweight mirror of audit_compliance_mappings.py)
# ---------------------------------------------------------------------------


class RegulationsCatalogue:
    """Index over ``data/regulations.json`` for gap analysis."""

    def __init__(self, raw: Mapping[str, Any]) -> None:
        self._raw = raw
        self._versions: List[RegVersion] = []
        self._alias_index: Dict[str, str] = {}
        self._build()

    @classmethod
    def load(cls, path: pathlib.Path = REGS_PATH) -> "RegulationsCatalogue":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(json.load(fh))

    def _build(self) -> None:
        for framework in self._raw.get("frameworks", []):
            fid = framework.get("id", "")
            short = framework.get("shortName", "")
            name = framework.get("name", "")
            tier = int(framework.get("tier", 3))

            # Collect alias candidates (shortName, id, name, aliases list).
            for alias in list(framework.get("aliases", [])) + [short, fid, name]:
                if not alias:
                    continue
                self._alias_index[alias.strip().lower()] = fid

            for ver in framework.get("versions", []):
                clauses = tuple(
                    ClauseEntry(
                        clause=c["clause"],
                        topic=c.get("topic", ""),
                        priority_weight=float(c.get("priorityWeight", 0.0)),
                    )
                    for c in ver.get("commonClauses", [])
                )
                self._versions.append(
                    RegVersion(
                        framework_id=fid,
                        short_name=short,
                        name=name,
                        tier=tier,
                        version=ver.get("version", ""),
                        authoritative_url=ver.get("authoritativeUrl", ""),
                        clauses=clauses,
                    )
                )

        for alias, fid in self._raw.get("aliasIndex", {}).items():
            if alias.startswith("$"):
                continue
            self._alias_index[alias.strip().lower()] = fid

    def resolve_framework(self, name: str) -> Optional[str]:
        key = (name or "").strip().lower()
        if not key:
            return None
        return self._alias_index.get(key)

    def versions(self) -> List[RegVersion]:
        return self._versions


# ---------------------------------------------------------------------------
# UC sidecar walking
# ---------------------------------------------------------------------------


def _iter_uc_sidecars() -> Iterable[pathlib.Path]:
    return sorted(USE_CASES_DIR.glob("cat-*/uc-*.json"))


def _collect_uc_hits(
    catalogue: RegulationsCatalogue,
) -> Dict[Tuple[str, str, str], List[UcComplianceHit]]:
    """Return (framework_id, version, clause) -> hits[]."""

    hits: Dict[Tuple[str, str, str], List[UcComplianceHit]] = defaultdict(list)
    for path in _iter_uc_sidecars():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except Exception:
            continue
        uc_id = str(doc.get("id", path.stem))
        status = str(doc.get("status", "") or "__unset__")
        for entry in doc.get("compliance", []) or []:
            reg_name = entry.get("regulation", "")
            version = str(entry.get("version", ""))
            clause = str(entry.get("clause", "")).strip()
            if not clause:
                continue
            fid = catalogue.resolve_framework(reg_name)
            if not fid:
                continue
            assurance = str(entry.get("assurance", "") or "").strip().lower()
            mode = str(entry.get("mode", "") or "").strip()
            hits[(fid, version, clause)].append(
                UcComplianceHit(
                    uc_id=uc_id,
                    status=status,
                    assurance=assurance,
                    mode=mode,
                )
            )
    return hits


# ---------------------------------------------------------------------------
# Gap computation
# ---------------------------------------------------------------------------


def _rank_assurance(values: Sequence[str]) -> Optional[str]:
    best: Optional[str] = None
    best_rank = -1
    for v in values:
        key = (v or "").strip().lower()
        if not key:
            continue
        rank = ASSURANCE_RANK.get(key, 0)
        if rank > best_rank:
            best_rank = rank
            best = key
    return best


def _build_gaps(
    version: RegVersion,
    hits: Mapping[Tuple[str, str, str], List[UcComplianceHit]],
) -> List[ClauseGap]:
    out: List[ClauseGap] = []
    for ce in version.clauses:
        bucket = hits.get((version.framework_id, version.version, ce.clause), [])
        uc_ids: List[str] = []
        draft_ids: List[str] = []
        assurances: List[str] = []
        for h in bucket:
            if h.multiplier > 0.0:
                uc_ids.append(h.uc_id)
                assurances.append(h.assurance)
            else:
                draft_ids.append(h.uc_id)
        out.append(
            ClauseGap(
                clause=ce.clause,
                topic=ce.topic,
                priority_weight=ce.priority_weight,
                uc_ids=sorted(set(uc_ids)),
                draft_uc_ids=sorted(set(draft_ids)),
                max_assurance=_rank_assurance(assurances),
            )
        )
    return out


def _compute_report(catalogue: RegulationsCatalogue) -> Dict[str, Any]:
    hits = _collect_uc_hits(catalogue)

    tiers: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for version in sorted(
        catalogue.versions(),
        key=lambda rv: (rv.tier, rv.framework_id, rv.version),
    ):
        tier_label = f"tier-{version.tier}"
        bucket = tiers[tier_label].setdefault(version.framework_id, {
            "short_name": version.short_name,
            "name": version.name,
            "tier": version.tier,
            "versions": {},
        })
        gaps = _build_gaps(version, hits)
        total = len(gaps)
        covered = sum(1 for g in gaps if g.covered)
        weight_total = round(sum(g.priority_weight for g in gaps), 4)
        weight_covered = round(
            sum(g.priority_weight for g in gaps if g.covered), 4
        )
        bucket["versions"][version.version] = {
            "authoritative_url": version.authoritative_url,
            "clauses": [g.to_json() for g in gaps],
            "common_clause_count": total,
            "covered_count": covered,
            "coverage_pct": round((covered / total) * 100.0, 2) if total else 0.0,
            "priority_weight_covered": weight_covered,
            "priority_weight_pct": round(
                (weight_covered / weight_total) * 100.0, 2
            ) if weight_total else 0.0,
            "priority_weight_total": weight_total,
        }

    # Roll-ups per tier: sum across all versions in the tier.
    rollups: Dict[str, Any] = {}
    for tier_label, frameworks in tiers.items():
        total_cl = 0
        covered_cl = 0
        total_w = 0.0
        covered_w = 0.0
        for fw in frameworks.values():
            for v in fw["versions"].values():
                total_cl += v["common_clause_count"]
                covered_cl += v["covered_count"]
                total_w += v["priority_weight_total"]
                covered_w += v["priority_weight_covered"]
        rollups[tier_label] = {
            "common_clause_count": total_cl,
            "covered_count": covered_cl,
            "coverage_pct": round((covered_cl / total_cl) * 100.0, 2) if total_cl else 0.0,
            "priority_weight_covered": round(covered_w, 4),
            "priority_weight_pct": round(
                (covered_w / total_w) * 100.0, 2
            ) if total_w else 0.0,
            "priority_weight_total": round(total_w, 4),
        }

    return {
        "generated_utc": _generated_timestamp(),
        "rollups": rollups,
        "schema_version": "1.0.0",
        "tiers": tiers,
    }


# ---------------------------------------------------------------------------
# Deterministic timestamp (SOURCE_DATE_EPOCH fallback)
# ---------------------------------------------------------------------------


def _generated_timestamp() -> str:
    """Use SOURCE_DATE_EPOCH when present, otherwise the committed timestamp
    of ``data/regulations.json``.  Both fall back to a fixed sentinel so a
    dirty working tree still produces a stable string.
    """

    import os
    import subprocess

    env = os.environ.get("SOURCE_DATE_EPOCH")
    if env and env.isdigit():
        return dt.datetime.fromtimestamp(int(env), dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(REGS_PATH.relative_to(REPO_ROOT))],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        stamp = (out.stdout or "").strip()
        if stamp.isdigit():
            return dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except Exception:
        pass
    return "1970-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _render_markdown(report: Mapping[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Compliance clause-level gap analysis")
    lines.append("")
    lines.append(f"_Generated: {report['generated_utc']}_ by "
                 "`scripts/audit_compliance_gaps.py`. Do not hand-edit.")
    lines.append("")
    lines.append("This report inverts the compliance coverage audit: for every "
                 "regulation-version listed in `data/regulations.json` it walks "
                 "every `commonClauses[]` entry and records whether at least "
                 "one non-draft UC sidecar tags that clause. Gaps are ranked by "
                 "the clause's `priorityWeight` so authoring effort can focus on "
                 "the highest-impact worklist items.")
    lines.append("")

    lines.append("## Tier rollups")
    lines.append("")
    lines.append("| Tier | Clauses | Covered | Coverage % | Priority weight | Priority covered | Priority % |")
    lines.append("|------|--------:|--------:|-----------:|----------------:|------------------:|-----------:|")
    for tier_label in sorted(report["rollups"].keys()):
        r = report["rollups"][tier_label]
        lines.append(
            f"| {tier_label} | {r['common_clause_count']} | {r['covered_count']} | "
            f"{r['coverage_pct']:.2f} | {r['priority_weight_total']:.4f} | "
            f"{r['priority_weight_covered']:.4f} | {r['priority_weight_pct']:.2f} |"
        )
    lines.append("")

    for tier_label in sorted(report["tiers"].keys()):
        lines.append(f"## {tier_label.capitalize().replace('-', ' ')} frameworks")
        lines.append("")
        frameworks = report["tiers"][tier_label]
        for fid in sorted(frameworks.keys()):
            fw = frameworks[fid]
            lines.append(f"### {fw['short_name']} — `{fid}`")
            lines.append("")
            lines.append(f"_{fw['name']}_")
            lines.append("")
            for version in sorted(fw["versions"].keys()):
                v = fw["versions"][version]
                lines.append(f"#### {fw['short_name']}@{version}")
                lines.append("")
                lines.append(f"- Common clauses: **{v['common_clause_count']}**")
                lines.append(f"- Covered: **{v['covered_count']}** "
                             f"({v['coverage_pct']:.2f}%)")
                lines.append(f"- Priority-weighted coverage: "
                             f"**{v['priority_weight_pct']:.2f}%** "
                             f"({v['priority_weight_covered']:.4f} / "
                             f"{v['priority_weight_total']:.4f})")
                if v.get("authoritative_url"):
                    lines.append(f"- Authoritative source: "
                                 f"{v['authoritative_url']}")
                lines.append("")
                lines.append("| Clause | Topic | Priority | UCs | Top assurance | Sample UCs |")
                lines.append("|--------|-------|---------:|----:|---------------|------------|")
                for c in v["clauses"]:
                    sample = ", ".join(c["uc_ids"]) if c["uc_ids"] else "—"
                    assurance = c.get("max_assurance") or "—"
                    covered_marker = "✔" if c["covered"] else "✖"
                    lines.append(
                        f"| `{c['clause']}` | {c['topic']} | "
                        f"{c['priority_weight']:.2f} | "
                        f"{covered_marker} {c['uc_count']} | {assurance} | "
                        f"{sample} |"
                    )
                lines.append("")
                # Top missing clauses ranked by priority weight.
                missing = [c for c in v["clauses"] if not c["covered"]]
                if missing:
                    missing.sort(
                        key=lambda c: (-c["priority_weight"], c["clause"])
                    )
                    lines.append("<details><summary>Top gaps (ranked by priority weight)</summary>")
                    lines.append("")
                    lines.append("| Priority | Clause | Topic |")
                    lines.append("|---------:|--------|-------|")
                    for c in missing[:12]:
                        lines.append(
                            f"| {c['priority_weight']:.2f} | "
                            f"`{c['clause']}` | {c['topic']} |"
                        )
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_This file is generated by `scripts/audit_compliance_gaps.py`. "
                 "See `docs/coverage-methodology.md` for clause / priority / "
                 "assurance definitions._")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Writers + check mode
# ---------------------------------------------------------------------------


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write_report(report: Mapping[str, Any], *, json_path: pathlib.Path, md_path: pathlib.Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(_canonical_json(report), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")


def _check_drift(report: Mapping[str, Any]) -> int:
    """Regenerate into a tempdir, diff against the committed tree."""

    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="compliance-gaps-check-"))
    json_tmp = tmp_dir / "compliance-gaps.json"
    md_tmp = tmp_dir / "compliance-gaps.md"
    _write_report(report, json_path=json_tmp, md_path=md_tmp)

    rc = 0
    for live, tmp in [(REPORT_JSON, json_tmp), (REPORT_MD, md_tmp)]:
        if not live.exists():
            print(
                "Compliance gap report drift — missing committed file: "
                f"{live.relative_to(REPO_ROOT)}",
                file=sys.stderr,
            )
            rc = 1
            continue
        live_text = live.read_text(encoding="utf-8")
        tmp_text = tmp.read_text(encoding="utf-8")
        if live_text != tmp_text:
            print(
                "Compliance gap report drift detected — regenerate with "
                "`python3 scripts/audit_compliance_gaps.py` and commit:",
                file=sys.stderr,
            )
            print(f"  differs: {live.relative_to(REPO_ROOT)}", file=sys.stderr)
            rc = 1
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate into a tempdir and diff against the committed tree.",
    )
    parser.add_argument(
        "--json-out",
        type=pathlib.Path,
        default=REPORT_JSON,
        help=f"Output JSON report path (default: {REPORT_JSON})",
    )
    parser.add_argument(
        "--md-out",
        type=pathlib.Path,
        default=REPORT_MD,
        help=f"Output markdown report path (default: {REPORT_MD})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = _parse_args(argv)

    if not REGS_PATH.exists():
        print(f"error: {REGS_PATH} is missing", file=sys.stderr)
        return 1

    catalogue = RegulationsCatalogue.load(REGS_PATH)
    report = _compute_report(catalogue)

    if args.check:
        return _check_drift(report)

    _write_report(report, json_path=args.json_out, md_path=args.md_out)
    rollups = report["rollups"]
    print("Compliance gap analysis")
    for tier_label in sorted(rollups.keys()):
        r = rollups[tier_label]
        if not r["common_clause_count"]:
            print(
                f"  {tier_label:6s}  no common clauses defined — not applicable"
            )
            continue
        print(
            f"  {tier_label:6s}  clauses={r['common_clause_count']:>4d}  "
            f"covered={r['covered_count']:>4d}  "
            f"coverage%={r['coverage_pct']:>6.2f}  "
            f"priority%={r['priority_weight_pct']:>6.2f}"
        )
    print(f"  wrote {args.json_out.relative_to(REPO_ROOT)}")
    print(f"  wrote {args.md_out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
