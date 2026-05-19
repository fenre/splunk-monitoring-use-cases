#!/usr/bin/env python3
"""Validate dist/observability/* artefacts for shape and plausible bounds.

Companion to ``generate-observability-metrics``. CI runs this after
generation to catch malformed JSON, impossible quantiles, or drift in
the Prometheus textfile format.

Usage::

    python -m splunk_uc audit-observability-drift --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DIR = REPO_ROOT / "dist" / "observability"

PROM_LINE_RE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?P<labels>\{[^}]*\})?\s+"
    r"(?P<value>-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)(?:\s+(?P<ts>\d+))?$"
)


@dataclass(frozen=True)
class Issue:
    code: str
    message: str


def validate_freshness(freshness: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    total = freshness.get("totalUseCases")
    if not isinstance(total, int) or total < 0:
        issues.append(Issue("freshness-total", "totalUseCases must be a non-negative integer"))
        return issues

    quantiles = freshness.get("quantiles", {})
    if isinstance(quantiles, dict):
        p25 = quantiles.get("p25")
        p50 = quantiles.get("p50")
        p75 = quantiles.get("p75")
        p95 = quantiles.get("p95")
        for label, val in (("p25", p25), ("p50", p50), ("p75", p75), ("p95", p95)):
            if not isinstance(val, (int, float)) or val < 0:
                issues.append(Issue("freshness-quantile", f"quantiles.{label} must be a non-negative number"))
        if (
            isinstance(p25, (int, float))
            and isinstance(p50, (int, float))
            and isinstance(p75, (int, float))
            and isinstance(p95, (int, float))
        ):
            nums = (float(p25), float(p50), float(p75), float(p95))
            if not (nums[0] <= nums[1] <= nums[2] <= nums[3]):
                issues.append(Issue("freshness-monotone", "quantiles must be monotone non-decreasing"))

    buckets = freshness.get("ageBuckets", {})
    if isinstance(buckets, dict):
        bucket_sum = sum(v for v in buckets.values() if isinstance(v, int))
        if bucket_sum != total:
            issues.append(
                Issue(
                    "freshness-buckets",
                    f"ageBuckets sum ({bucket_sum}) must equal totalUseCases ({total})",
                )
            )

    oldest = freshness.get("oldest", [])
    newest = freshness.get("newest", [])
    if total > 0:
        if not isinstance(oldest, list) or len(oldest) == 0:
            issues.append(Issue("freshness-oldest", "oldest must be a non-empty list when totalUseCases > 0"))
        if not isinstance(newest, list) or len(newest) == 0:
            issues.append(Issue("freshness-newest", "newest must be a non-empty list when totalUseCases > 0"))

    return issues


def validate_quality(quality: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    by_cat = quality.get("byCategoryCriticality", {})
    if not isinstance(by_cat, dict):
        issues.append(Issue("quality-shape", "byCategoryCriticality must be an object"))
        return issues

    for cat, crits in by_cat.items():
        if not isinstance(crits, dict):
            continue
        for crit, block in crits.items():
            if not isinstance(block, dict):
                continue
            tiers = ("gold", "silver", "bronze", "none")
            tier_sum = sum(block.get(t, 0) for t in tiers if isinstance(block.get(t), int))
            total = block.get("total")
            if isinstance(total, int) and tier_sum != total:
                issues.append(
                    Issue(
                        "quality-tier-sum",
                        f"category {cat} criticality {crit}: tier counts ({tier_sum}) != total ({total})",
                    )
                )
            dist = block.get("distribution", {})
            if isinstance(dist, dict) and total:
                pct_sum = sum(dist.get(t, 0.0) for t in tiers if isinstance(dist.get(t), (int, float)))
                if abs(pct_sum - 100.0) > 0.1:
                    issues.append(
                        Issue(
                            "quality-distribution",
                            f"category {cat} criticality {crit}: distribution sums to {pct_sum:.1f}, expected 100 ± 0.1",
                        )
                    )

    bronze_heavy = quality.get("bronzeHeavyCategories", [])
    if not isinstance(bronze_heavy, list):
        issues.append(Issue("quality-bronze-heavy", "bronzeHeavyCategories must be a list"))

    return issues


def validate_coverage(coverage: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    dimensions = coverage.get("dimensions", [])
    if not isinstance(dimensions, list):
        issues.append(Issue("coverage-dimensions", "dimensions must be a list"))
        return issues

    per_dim = coverage.get("perDimension", {})
    if isinstance(per_dim, dict):
        for dim, block in per_dim.items():
            if dim not in dimensions:
                issues.append(Issue("coverage-dimension-extra", f"perDimension key {dim!r} not in dimensions list"))
            if isinstance(block, dict):
                pct = block.get("percentage")
                if isinstance(pct, (int, float)) and not (0 <= pct <= 100):
                    issues.append(Issue("coverage-pct-range", f"perDimension.{dim}.percentage out of [0, 100]"))

    matrix_pct = coverage.get("matrixPercentages", {})
    matrix_counts = coverage.get("matrixCounts", {})
    if isinstance(matrix_pct, dict):
        for cat, row in matrix_pct.items():
            if not isinstance(row, dict):
                continue
            for dim in row:
                if dim not in dimensions:
                    issues.append(
                        Issue("coverage-matrix-dim", f"matrixPercentages[{cat}] has unknown dimension {dim!r}")
                    )
            if isinstance(matrix_counts, dict) and cat in matrix_counts:
                count_row = matrix_counts[cat]
                if isinstance(count_row, dict) and set(count_row.keys()) != set(row.keys()):
                    issues.append(
                        Issue(
                            "coverage-matrix-mismatch",
                            f"matrixCounts/matrixPercentages key mismatch for category {cat}",
                        )
                    )

    return issues


def validate_prometheus(text: str) -> list[Issue]:
    issues: list[Issue] = []
    families_with_help: set[str] = set()
    families_with_type: set[str] = set()
    metric_names: set[str] = set()

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# HELP "):
            parts = line.split(" ", 3)
            if len(parts) >= 3:
                families_with_help.add(parts[2])
            continue
        if line.startswith("# TYPE "):
            parts = line.split(" ", 3)
            if len(parts) >= 3:
                families_with_type.add(parts[2])
            continue
        if line.startswith("#"):
            issues.append(Issue("prom-comment", f"line {lineno}: unsupported comment {line!r}"))
            continue
        if not PROM_LINE_RE.match(line):
            issues.append(Issue("prom-line", f"line {lineno}: does not match Prometheus exposition format"))
            continue
        name = PROM_LINE_RE.match(line).group("name")  # type: ignore[union-attr]
        metric_names.add(name)

    for family in metric_names:
        if family not in families_with_help:
            issues.append(Issue("prom-help", f"missing # HELP for metric family {family!r}"))
        if family not in families_with_type:
            issues.append(Issue("prom-type", f"missing # TYPE for metric family {family!r}"))

    return issues


def audit_directory(obs_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    freshness_path = obs_dir / "freshness.json"
    quality_path = obs_dir / "quality.json"
    coverage_path = obs_dir / "coverage.json"
    prom_path = obs_dir / "catalogue.prom"

    for path in (freshness_path, quality_path, coverage_path, prom_path):
        if not path.is_file():
            issues.append(Issue("missing-file", f"missing {path.relative_to(REPO_ROOT)}"))
            return issues

    try:
        freshness = json.loads(freshness_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(Issue("freshness-json", f"freshness.json: {exc}"))
        freshness = {}

    try:
        quality = json.loads(quality_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(Issue("quality-json", f"quality.json: {exc}"))
        quality = {}

    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(Issue("coverage-json", f"coverage.json: {exc}"))
        coverage = {}

    prom_text = prom_path.read_text(encoding="utf-8")

    if isinstance(freshness, dict):
        issues.extend(validate_freshness(freshness))
    if isinstance(quality, dict):
        issues.extend(validate_quality(quality))
    if isinstance(coverage, dict):
        issues.extend(validate_coverage(coverage))
    issues.extend(validate_prometheus(prom_text))

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when validation issues are found (default behaviour).",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_DIR,
        help=f"Observability output directory (default: {DEFAULT_DIR.relative_to(REPO_ROOT)}).",
    )
    args = parser.parse_args(argv)

    issues = audit_directory(args.dir)
    if issues:
        for issue in issues:
            print(f"ERROR {issue.code}: {issue.message}", file=sys.stderr)
        return 1

    print(f"OK: observability artefacts valid under {args.dir.relative_to(REPO_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
