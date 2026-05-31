#!/usr/bin/env python3
"""Cost-field coverage audit for UC sidecars.

Walks ``content/cat-*/UC-*.json`` and classifies each UC into:

* **complete** — ``cost`` is an object with a non-empty ``tier``.
* **partial** — ``cost`` is present but ``tier`` is absent or blank.
* **missing** — no ``cost`` key (or ``cost`` is null / not an object).

Emits a machine report at ``dist/audits/cost-coverage.json`` and a human
markdown rollup at ``dist/audits/cost-coverage.md`` listing the top missing
and partial UCs grouped by category and criticality.

Threshold ratchet (Lane N backfill)
-----------------------------------

CI starts at ``--threshold 0`` (warn-only — any non-negative coverage passes).
As Lane N hand-populates ``cost.tier`` on sidecars, maintainers ratchet the
threshold upward in follow-up PRs (same pattern as
``audit-coverage-budget`` baselines). At threshold *N*, ``--check`` exits 1
when fewer than *N* percent of UCs carry ``cost.tier``.

Usage::

    python3 -m splunk_uc audit-cost-coverage
    python3 -m splunk_uc audit-cost-coverage --check --threshold 0
    python3 -m splunk_uc audit-cost-coverage --out /tmp/cost-coverage.json

Exit codes
----------

* ``0`` — report written (if not ``--check``-only failure) and tier coverage
  meets the threshold.
* ``1`` — tier coverage below ``--threshold``.
* ``2`` — usage / I/O error.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTENT_ROOT = REPO_ROOT / "content"
DEFAULT_JSON_OUT = REPO_ROOT / "dist" / "audits" / "cost-coverage.json"
DEFAULT_MD_OUT = REPO_ROOT / "dist" / "audits" / "cost-coverage.md"

CoverageStatus = Literal["complete", "partial", "missing"]
VALID_TIERS = frozenset({"low", "medium", "high", "extreme"})
TOP_N = 25


@dataclass(frozen=True)
class UcCostEntry:
    uc_id: str
    category: int
    criticality: str
    status: CoverageStatus
    title: str


@dataclass(frozen=True)
class CostCoverageReport:
    total: int
    complete: int
    partial: int
    missing: int
    tier_coverage_pct: float
    entries: tuple[UcCostEntry, ...]

    def to_json_dict(self) -> dict[str, Any]:
        by_category: dict[str, dict[str, int]] = {}
        for entry in self.entries:
            cat_key = str(entry.category)
            bucket = by_category.setdefault(
                cat_key,
                {"complete": 0, "partial": 0, "missing": 0, "total": 0},
            )
            bucket[entry.status] += 1
            bucket["total"] += 1

        queue = [
            {
                "uc_id": e.uc_id,
                "category": e.category,
                "criticality": e.criticality,
                "status": e.status,
                "title": e.title,
            }
            for e in self.entries
            if e.status != "complete"
        ]

        return {
            "schemaVersion": "1.0",
            "summary": {
                "total": self.total,
                "complete": self.complete,
                "partial": self.partial,
                "missing": self.missing,
                "tier_coverage_pct": round(self.tier_coverage_pct, 2),
            },
            "by_category": dict(sorted(by_category.items(), key=lambda kv: int(kv[0]))),
            "queue": queue,
        }


def _category_from_path(path: Path) -> int:
    name = path.parent.name
    if not name.startswith("cat-"):
        return 0
    try:
        return int(name.split("-", 2)[1])
    except (IndexError, ValueError):
        return 0


def _classify_cost(cost: Any) -> CoverageStatus:
    if not isinstance(cost, dict):
        return "missing"
    tier = cost.get("tier")
    if isinstance(tier, str) and tier.strip() in VALID_TIERS:
        return "complete"
    return "partial"


def evaluate_coverage(content_root: Path) -> CostCoverageReport:
    """Walk UC sidecars under *content_root* and classify cost coverage."""
    paths = sorted(content_root.glob("cat-*/UC-*.json"))
    entries: list[UcCostEntry] = []

    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue

        uc_id = payload.get("id")
        if not isinstance(uc_id, str) or not uc_id:
            stem = path.stem
            uc_id = stem[3:] if stem.startswith("UC-") else stem

        title = payload.get("title")
        if not isinstance(title, str):
            title = ""

        criticality = payload.get("criticality")
        if not isinstance(criticality, str):
            criticality = "unknown"

        status = _classify_cost(payload.get("cost"))
        entries.append(
            UcCostEntry(
                uc_id=uc_id,
                category=_category_from_path(path),
                criticality=criticality,
                status=status,
                title=title,
            )
        )

    entries.sort(key=lambda e: (e.category, e.uc_id))
    complete = sum(1 for e in entries if e.status == "complete")
    partial = sum(1 for e in entries if e.status == "partial")
    missing = sum(1 for e in entries if e.status == "missing")
    total = len(entries)
    tier_pct = (complete / total * 100.0) if total else 0.0

    return CostCoverageReport(
        total=total,
        complete=complete,
        partial=partial,
        missing=missing,
        tier_coverage_pct=tier_pct,
        entries=tuple(entries),
    )


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: CostCoverageReport) -> str:
    lines = [
        "# Cost field coverage",
        "",
        f"- Total UCs scanned: **{report.total}**",
        f"- Complete (`cost.tier` set): **{report.complete}** "
        f"({report.tier_coverage_pct:.1f}%)",
        f"- Partial (`cost` without tier): **{report.partial}**",
        f"- Missing (no `cost`): **{report.missing}**",
        "",
        "## Top missing / partial UCs (by category, then criticality)",
        "",
    ]

    pending = [e for e in report.entries if e.status != "complete"]
    crit_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    pending.sort(
        key=lambda e: (
            e.category,
            crit_rank.get(e.criticality, 9),
            e.uc_id,
        )
    )

    shown = pending[:TOP_N]
    if not shown:
        lines.append("_All UCs have a complete `cost.tier`._")
    else:
        lines.append("| UC ID | Cat | Criticality | Status | Title |")
        lines.append("|-------|-----|-------------|--------|-------|")
        for entry in shown:
            title = entry.title.replace("|", "\\|")
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(
                f"| UC-{entry.uc_id} | {entry.category} | "
                f"{entry.criticality} | {entry.status} | {title} |"
            )
        if len(pending) > TOP_N:
            lines.append("")
            lines.append(f"_… and {len(pending) - TOP_N} more._")

    lines.append("")
    return "\n".join(lines)


def write_reports(
    report: CostCoverageReport,
    json_path: Path,
    md_path: Path | None = None,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        _canonical_json(report.to_json_dict()),
        encoding="utf-8",
    )
    md_target = md_path if md_path is not None else json_path.with_suffix(".md")
    md_target.write_text(render_markdown(report), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help=f"UC sidecar root (default: {DEFAULT_CONTENT_ROOT})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_JSON_OUT,
        help=f"JSON report path (default: {DEFAULT_JSON_OUT})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when tier coverage is below --threshold.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum percent of UCs with cost.tier (default: 0, warn-only).",
    )
    args = parser.parse_args(argv)

    if not args.content_root.is_dir():
        print(f"ERROR: content root not found: {args.content_root}", file=sys.stderr)
        return 2

    report = evaluate_coverage(args.content_root)
    write_reports(report, args.out)

    print(
        f"Cost coverage: {report.complete}/{report.total} complete "
        f"({report.tier_coverage_pct:.1f}% tier coverage); "
        f"partial={report.partial}, missing={report.missing}"
    )
    print(f"Wrote {args.out}")
    print(f"Wrote {args.out.with_suffix('.md')}")

    if args.check and report.tier_coverage_pct < args.threshold:
        print(
            f"FAIL: tier coverage {report.tier_coverage_pct:.1f}% "
            f"is below threshold {args.threshold:.1f}%",
            file=sys.stderr,
        )
        return 1

    if report.tier_coverage_pct < args.threshold:
        print(
            f"WARN: tier coverage {report.tier_coverage_pct:.1f}% "
            f"is below threshold {args.threshold:.1f}% (pass --check to fail CI)",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
