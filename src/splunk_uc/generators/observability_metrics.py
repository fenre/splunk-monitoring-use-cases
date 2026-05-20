#!/usr/bin/env python3
"""Emit orthogonal catalogue observability metrics alongside dist/metrics.json.

Three JSON families (freshness, quality, coverage) plus a Prometheus text
exposition file live under ``dist/observability/``. They deliberately do
**not** duplicate the rollups already in ``dist/metrics.json`` — see
``schemas/v2/metrics.schema.json`` and ``docs/observability.md``.

Usage::

    python -m splunk_uc generate-observability-metrics
    python -m splunk_uc generate-observability-metrics --check
    python -m splunk_uc generate-observability-metrics --limit 200 --family freshness
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from statistics import quantiles
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
VERSION_PATH = REPO_ROOT / "VERSION"
DEFAULT_OUT = REPO_ROOT / "dist" / "observability"

FRESHNESS_SCHEMA_VERSION = "1.0.0"
QUALITY_SCHEMA_VERSION = "1.0.0"
COVERAGE_SCHEMA_VERSION = "1.0.0"

Family = Literal["freshness", "quality", "coverage", "prometheus", "all"]

COVERAGE_DIMENSIONS: tuple[str, ...] = (
    "cost",
    "compliance",
    "mitreAttack",
    "equipmentModels",
    "controlTest",
    "evidence",
    "references",
    "knownFalsePositives",
    "exclusions",
    "detailedImplementation",
    "prerequisites",
)

CRITICALITY_VALUES: tuple[str, ...] = ("critical", "high", "medium", "low", "unknown")

TOP_N = 25


def _read_version() -> str:
    if VERSION_PATH.is_file():
        return VERSION_PATH.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _git_head_epoch() -> int | None:
    try:
        proc = subprocess.run(
            ["git", "--no-pager", "log", "-1", "--format=%ct"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip().isdigit():
            return int(proc.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _reproducible_now() -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    ts: int
    if epoch and epoch.isdigit():
        ts = int(epoch)
    elif (head := _git_head_epoch()) is not None:
        ts = head
    else:
        ts = int(datetime.now(UTC).timestamp())
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _reproducible_today() -> date:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=UTC).date()
    head = _git_head_epoch()
    if head is not None:
        return datetime.fromtimestamp(head, tz=UTC).date()
    return datetime.now(UTC).date()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _parse_uc_sort_key(uc_id: str) -> tuple[int, int, int, str]:
    parts = uc_id.split(".")
    if len(parts) != 3:
        return (999, 999, 999, uc_id)
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]), uc_id)
    except ValueError:
        return (999, 999, 999, uc_id)


def _category_from_path(path: Path) -> str:
    name = path.parent.name
    if name.startswith("cat-"):
        segment = name.split("-", 1)[1]
        digits = segment.split("-", 1)[0]
        if digits.isdigit():
            return digits.zfill(2)
    return "00"


def _iter_sidecar_paths(limit: int | None = None) -> list[Path]:
    """Return sidecar paths sorted deterministically, optionally capped per category."""
    by_category: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(CONTENT_DIR.glob("cat-*/UC-*.json")):
        by_category[_category_from_path(path)].append(path)
    out: list[Path] = []
    for cat in sorted(by_category):
        paths = sorted(by_category[cat], key=lambda p: p.stem)
        if limit is not None and limit > 0:
            paths = paths[:limit]
        out.extend(paths)
    return out


def _git_last_modified(path: Path) -> tuple[str | None, str]:
    """Return (ISO-8601 timestamp, source) from git or mtime fallback."""
    rel = path.relative_to(REPO_ROOT)
    try:
        proc = subprocess.run(
            [
                "git",
                "--no-pager",
                "log",
                "-1",
                "--format=%cI",
                "--",
                str(rel),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if proc.returncode == 0:
            ts = proc.stdout.strip()
            if ts:
                return ts, "git"
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        mtime = path.stat().st_mtime
        ts = datetime.fromtimestamp(mtime, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return ts, "mtime"
    except OSError:
        return None, "unavailable"


def _age_days(last_modified: str | None, reference: date) -> int | None:
    if not last_modified:
        return None
    try:
        if last_modified.endswith("Z"):
            dt = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(last_modified)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        delta = (reference - dt.date()).days
        return max(0, delta)
    except ValueError:
        return None


def _compute_quantiles(ages: list[int]) -> dict[str, float]:
    if not ages:
        return {"p25": 0.0, "p50": 0.0, "p75": 0.0, "p95": 0.0}
    sorted_ages = sorted(ages)
    if len(sorted_ages) == 1:
        val = float(sorted_ages[0])
        return {"p25": val, "p50": val, "p75": val, "p95": val}
    q = quantiles(sorted_ages, n=100, method="inclusive")
    return {
        "p25": float(q[24]),
        "p50": float(q[49]),
        "p75": float(q[74]),
        "p95": float(q[94]),
    }


def _exclusive_age_buckets(ages: list[int]) -> dict[str, int]:
    buckets = {
        "under90Days": 0,
        "days90to179": 0,
        "days180to364": 0,
        "days365to719": 0,
        "days720Plus": 0,
    }
    for age in ages:
        if age < 90:
            buckets["under90Days"] += 1
        elif age < 180:
            buckets["days90to179"] += 1
        elif age < 365:
            buckets["days180to364"] += 1
        elif age < 720:
            buckets["days365to719"] += 1
        else:
            buckets["days720Plus"] += 1
    return buckets


def _cumulative_older_than(ages: list[int]) -> dict[str, int]:
    return {
        "olderThan90Days": sum(1 for a in ages if a > 90),
        "olderThan180Days": sum(1 for a in ages if a > 180),
        "olderThan365Days": sum(1 for a in ages if a > 365),
        "olderThan720Days": sum(1 for a in ages if a > 720),
    }


def build_freshness(paths: Iterable[Path], reference: date | None = None) -> dict[str, Any]:
    ref = reference or _reproducible_today()
    entries: list[dict[str, Any]] = []
    for path in paths:
        uc = json.loads(path.read_text(encoding="utf-8"))
        uc_id = str(uc.get("id", path.stem.removeprefix("UC-")))
        last_mod, source = _git_last_modified(path)
        age = _age_days(last_mod, ref)
        if age is None:
            continue
        entries.append(
            {
                "ucId": uc_id,
                "category": _category_from_path(path),
                "ageDays": age,
                "lastModified": last_mod,
                "source": source,
            }
        )

    ages = [e["ageDays"] for e in entries]
    entries.sort(key=lambda e: (-e["ageDays"], _parse_uc_sort_key(e["ucId"])))
    oldest = entries[:TOP_N]
    newest = sorted(
        entries,
        key=lambda e: (e["ageDays"], _parse_uc_sort_key(e["ucId"])),
    )[:TOP_N]

    return {
        "schema_version": FRESHNESS_SCHEMA_VERSION,
        "generatedAt": _reproducible_now(),
        "catalogueVersion": _read_version(),
        "referenceDate": ref.isoformat(),
        "totalUseCases": len(entries),
        "quantiles": _compute_quantiles(ages),
        "cumulativeOlderThan": _cumulative_older_than(ages),
        "ageBuckets": _exclusive_age_buckets(ages),
        "oldest": oldest,
        "newest": newest,
    }


def _normalise_criticality(raw: Any) -> str:
    if isinstance(raw, str) and raw.strip():
        val = raw.strip().lower()
        if val in CRITICALITY_VALUES[:-1]:
            return val
    return "unknown"


def _classify_tier(uc: dict[str, Any], path: Path) -> str:
    """Classify UC tier via gold_profile.audit_uc using this module's REPO_ROOT."""
    import splunk_uc.audits.gold_profile as gp

    prev_root = gp.REPO_ROOT
    gp.REPO_ROOT = REPO_ROOT
    try:
        tier = gp.audit_uc(uc, path).get("tier", "none")
    finally:
        gp.REPO_ROOT = prev_root
    if tier not in ("gold", "silver", "bronze", "none"):
        return "none"
    return str(tier)


def build_quality(paths: Iterable[Path]) -> dict[str, Any]:
    by_cat_crit: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"gold": 0, "silver": 0, "bronze": 0, "none": 0})
    )
    cat_totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"gold": 0, "silver": 0, "bronze": 0, "none": 0}
    )

    for path in paths:
        uc = json.loads(path.read_text(encoding="utf-8"))
        cat = _category_from_path(path)
        crit = _normalise_criticality(uc.get("criticality"))
        tier = _classify_tier(uc, path)
        by_cat_crit[cat][crit][tier] += 1
        cat_totals[cat][tier] += 1

    by_category_criticality: dict[str, Any] = {}
    for cat in sorted(by_cat_crit):
        crit_block: dict[str, Any] = {}
        for crit in sorted(by_cat_crit[cat]):
            counts = by_cat_crit[cat][crit]
            total = sum(counts.values())
            distribution = {
                tier: round((counts[tier] / total) * 100.0, 1) if total else 0.0
                for tier in ("gold", "silver", "bronze", "none")
            }
            crit_block[crit] = {
                **counts,
                "total": total,
                "distribution": distribution,
            }
        by_category_criticality[cat] = crit_block

    bronze_heavy: list[str] = []
    for cat in sorted(cat_totals):
        totals = cat_totals[cat]
        total = sum(totals.values())
        if total == 0:
            continue
        bronze_pct = (totals["bronze"] / total) * 100.0
        if bronze_pct > 60.0:
            bronze_heavy.append(cat)

    return {
        "schema_version": QUALITY_SCHEMA_VERSION,
        "generatedAt": _reproducible_now(),
        "catalogueVersion": _read_version(),
        "byCategoryCriticality": by_category_criticality,
        "bronzeHeavyCategories": bronze_heavy,
    }


def _dimension_populated(uc: dict[str, Any], dimension: str) -> bool:
    if dimension == "prerequisites":
        key = "prerequisiteUseCases"
    else:
        key = dimension
    value = uc.get(key)
    if value is None:
        return False
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return bool(value)


def build_coverage(paths: Iterable[Path]) -> dict[str, Any]:
    path_list = list(paths)
    total = len(path_list)
    dimension_counts = dict.fromkeys(COVERAGE_DIMENSIONS, 0)
    matrix: dict[str, dict[str, int]] = {
        cat: dict.fromkeys(COVERAGE_DIMENSIONS, 0) for cat in sorted({_category_from_path(p) for p in path_list})
    }

    for path in path_list:
        uc = json.loads(path.read_text(encoding="utf-8"))
        cat = _category_from_path(path)
        if cat not in matrix:
            matrix[cat] = dict.fromkeys(COVERAGE_DIMENSIONS, 0)
        for dim in COVERAGE_DIMENSIONS:
            if _dimension_populated(uc, dim):
                dimension_counts[dim] += 1
                matrix[cat][dim] += 1

    per_dimension_pct = {
        dim: round((dimension_counts[dim] / total) * 100.0, 2) if total else 0.0
        for dim in COVERAGE_DIMENSIONS
    }

    matrix_pct: dict[str, dict[str, float]] = {}
    cat_counts: dict[str, int] = defaultdict(int)
    for path in path_list:
        cat_counts[_category_from_path(path)] += 1

    for cat in sorted(matrix):
        cat_total = cat_counts.get(cat, 0)
        matrix_pct[cat] = {
            dim: round((matrix[cat][dim] / cat_total) * 100.0, 2) if cat_total else 0.0
            for dim in COVERAGE_DIMENSIONS
        }

    return {
        "schema_version": COVERAGE_SCHEMA_VERSION,
        "generatedAt": _reproducible_now(),
        "catalogueVersion": _read_version(),
        "totalUseCases": total,
        "dimensions": list(COVERAGE_DIMENSIONS),
        "perDimension": {
            dim: {"count": dimension_counts[dim], "percentage": per_dimension_pct[dim]}
            for dim in COVERAGE_DIMENSIONS
        },
        "matrixCounts": matrix,
        "matrixPercentages": matrix_pct,
    }


def render_prometheus(
    freshness: dict[str, Any],
    quality: dict[str, Any],
    coverage: dict[str, Any],
) -> str:
    lines: list[str] = []

    def emit(name: str, typ: str, help_text: str, samples: Iterable[tuple[str, float | int]]) -> None:
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} {typ}")
        for labels, value in samples:
            if labels:
                lines.append(f"{name}{{{labels}}} {value}")
            else:
                lines.append(f"{name} {value}")

    total = freshness.get("totalUseCases", 0)
    emit(
        "splunk_uc_total",
        "gauge",
        "Total use cases included in the observability snapshot.",
        [("", total)],
    )

    for q, key in (("0.25", "p25"), ("0.5", "p50"), ("0.75", "p75"), ("0.95", "p95")):
        val = freshness.get("quantiles", {}).get(key, 0.0)
        emit(
            "splunk_uc_freshness_age_days",
            "gauge",
            "Freshness age in days at the given quantile.",
            [(f'quantile="{q}"', val)],
        )

    for bucket, key in (
        ("under90", "under90Days"),
        ("90to179", "days90to179"),
        ("180to364", "days180to364"),
        ("365to719", "days365to719"),
        ("720plus", "days720Plus"),
    ):
        val = freshness.get("ageBuckets", {}).get(key, 0)
        emit(
            "splunk_uc_freshness_age_bucket",
            "gauge",
            "Exclusive freshness age bucket counts.",
            [(f'bucket="{bucket}"', val)],
        )

    for cat, crits in quality.get("byCategoryCriticality", {}).items():
        for crit, block in crits.items():
            for tier in ("gold", "silver", "bronze", "none"):
                emit(
                    "splunk_uc_quality_tier",
                    "gauge",
                    "UC count by category, criticality, and gold-profile tier.",
                    [(f'category="{cat}",criticality="{crit}",tier="{tier}"', block.get(tier, 0))],
                )

    for dim, block in coverage.get("perDimension", {}).items():
        emit(
            "splunk_uc_coverage_populated",
            "gauge",
            "Count of UCs with the optional dimension populated.",
            [(f'dimension="{dim}"', block.get("count", 0))],
        )
        emit(
            "splunk_uc_coverage_percentage",
            "gauge",
            "Percentage of UCs with the optional dimension populated.",
            [(f'dimension="{dim}"', block.get("percentage", 0.0))],
        )

    return "\n".join(lines) + "\n"


def _write_outputs(
    out_dir: Path,
    families: set[Family],
    freshness: dict[str, Any] | None,
    quality: dict[str, Any] | None,
    coverage: dict[str, Any] | None,
    prom: str | None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if freshness is not None:
        (out_dir / "freshness.json").write_text(_canonical_json(freshness), encoding="utf-8")
    if quality is not None:
        (out_dir / "quality.json").write_text(_canonical_json(quality), encoding="utf-8")
    if coverage is not None:
        (out_dir / "coverage.json").write_text(_canonical_json(coverage), encoding="utf-8")
    if prom is not None:
        (out_dir / "catalogue.prom").write_text(prom, encoding="utf-8")


def _read_if_exists(path: Path) -> str | None:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def generate(
    *,
    out_dir: Path,
    limit: int | None,
    family: Family,
    reference_date: date | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, str | None]:
    paths = _iter_sidecar_paths(limit=limit)
    if not paths:
        print("No UC sidecars found under content/", file=sys.stderr)
        return None, None, None, None

    freshness = quality = coverage = None
    prom: str | None = None

    want_all = family == "all"
    if want_all or family == "freshness":
        freshness = build_freshness(paths, reference=reference_date)
    if want_all or family == "quality":
        quality = build_quality(paths)
    if want_all or family == "coverage":
        coverage = build_coverage(paths)
    if want_all or family == "prometheus":
        if freshness is None:
            freshness = build_freshness(paths, reference=reference_date)
        if quality is None:
            quality = build_quality(paths)
        if coverage is None:
            coverage = build_coverage(paths)
        prom = render_prometheus(freshness, quality, coverage)

    return freshness, quality, coverage, prom


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when on-disk artefacts differ from a fresh generation.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT.relative_to(REPO_ROOT)}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Cap git/stat calls to N sidecars per category (fast iteration).",
    )
    parser.add_argument(
        "--family",
        choices=("freshness", "quality", "coverage", "prometheus", "all"),
        default="all",
        help="Emit only one artefact family (default: all).",
    )
    parser.add_argument(
        "--reference-date",
        type=str,
        default=None,
        help="Pin freshness age computation to YYYY-MM-DD (tests / reproducibility).",
    )
    args = parser.parse_args(argv)

    ref_date: date | None = None
    if args.reference_date:
        try:
            ref_date = date.fromisoformat(args.reference_date)
        except ValueError:
            print(f"Invalid --reference-date: {args.reference_date!r}", file=sys.stderr)
            return 2

    family: Family = args.family
    freshness, quality, coverage, prom = generate(
        out_dir=args.out,
        limit=args.limit,
        family=family,
        reference_date=ref_date,
    )
    if freshness is None and quality is None and coverage is None and prom is None:
        return 2

    expected: dict[str, str] = {}
    if freshness is not None:
        expected["freshness.json"] = _canonical_json(freshness)
    if quality is not None:
        expected["quality.json"] = _canonical_json(quality)
    if coverage is not None:
        expected["coverage.json"] = _canonical_json(coverage)
    if prom is not None:
        expected["catalogue.prom"] = prom

    if args.check:
        drift: list[str] = []
        for name, text in expected.items():
            on_disk = _read_if_exists(args.out / name)
            if on_disk != text:
                drift.append(name)
        if drift:
            print(
                f"FATAL: observability drift in {', '.join(drift)} — "
                "run python -m splunk_uc generate-observability-metrics",
                file=sys.stderr,
            )
            return 1
        print(f"OK: observability metrics up to date ({len(expected)} artefact(s)).")
        return 0

    _write_outputs(args.out, {family}, freshness, quality, coverage, prom)
    uc_count = (
        (freshness or {}).get("totalUseCases")
        or (coverage or {}).get("totalUseCases")
        or "?"
    )
    print(
        f"Wrote observability metrics to {args.out.relative_to(REPO_ROOT)} ({uc_count} UCs)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
