"""tools.build.render_metrics — emit ``dist/metrics.json``.

Per repo-overhaul plan §P8 (observability), every build emits a
top-line catalogue health snapshot to ``dist/metrics.json``. Unlike the
content-quality dimensions in ``scorecard.json`` (per-category depth,
references, samples) and the build-environment fields in
``BUILD-INFO.json`` (git SHA, schema versions, counts), ``metrics.json``
is the **trend-tracking** artifact:

* Top-level rollups (no per-category breakdown unless it's a small fixed
  list like ucsByCategory). The full per-category surface stays in
  scorecard.json.
* Numeric percentiles (p50/p90/p99) so a CI step or a stewardship
  dashboard can plot drift over releases without re-walking
  ``catalog.json`` itself.
* Top-N rollups (top regulations, top MITRE techniques, top equipment)
  capped at 10 entries — enough signal for a dashboard, small enough
  that a human can eyeball the diff in a PR.

Stability
---------
The schema is versioned via ``schema_version`` and validated against
``schemas/v2/metrics.schema.json`` (additive-only changes are non-
breaking; renaming or removing a field is a major bump). Field set is
sorted at emit time so two consecutive ``--reproducible`` builds
produce byte-identical bytes.

Reproducibility
---------------
The emitter is pure — it depends only on the in-memory ``Catalog``
that ``parse_content`` produced. ``generatedAt`` is the only volatile
field, and it's frozen to ``catalog.git_commit_iso`` (or HEAD's commit
time) when ``reproducible=True``.

Why this lives in ``tools/build``
---------------------------------
Trend metrics are an output artifact of the build pipeline; they share
the Catalog walk, the reproducible-timestamp helpers, and the schema
conventions used by ``BUILD-INFO.json``. Putting them in a top-level
``scripts/`` audit would force a second catalog parse + a second pass
over 7 600 UCs, plus a fragile coupling to the live ``dist/`` tree.
"""

from __future__ import annotations

import json
import math
import platform
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .parse_content import Catalog

SCHEMA_VERSION = "1.0.0"
SCHEMA_REF = "/schemas/v2/metrics.schema.json"

# Top-N caps for "leader-board" rollups. Held small so a human can
# eyeball the diff in a PR; consumers needing the long tail go to
# scorecard.json or to dist/api/v1/.
_TOP_N_REGULATIONS = 10
_TOP_N_MITRE = 10
_TOP_N_CIM = 10
_TOP_N_EQUIPMENT = 10

# Quality-tier vocabulary — must match parse_content._inject_quality_scores().
_QUALITY_TIERS: tuple[str, ...] = ("gold", "silver", "bronze", "none")

# Wave vocabulary — must match schemas/uc.schema.json#wave.
_WAVE_TIERS: tuple[str, ...] = ("crawl", "walk", "run")


# ---------------------------------------------------------------------------
# Top-level emitter
# ---------------------------------------------------------------------------

def render(
    catalog: Catalog,
    out_dir: Path,
    *,
    reproducible: bool = False,
) -> Path:
    """Emit ``out_dir / metrics.json`` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_metrics(catalog, reproducible=reproducible)
    out_path = out_dir / "metrics.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def build_metrics(catalog: Catalog, *, reproducible: bool = False) -> dict[str, Any]:
    """Compute the metrics payload from an in-memory ``Catalog``.

    Pure function: no filesystem writes, no globals mutated. Useful for
    the unit tests that don't want a temp dir.
    """
    ucs = list(catalog.iter_ucs())

    counts = _counts(catalog, ucs)
    quality = _quality_block(ucs)
    coverage = _coverage_block(ucs)
    distributions = _distributions_block(ucs)
    by_category = _ucs_by_category(catalog)
    leaders = _leaderboards(ucs)

    payload: dict[str, Any] = {
        "$schema": SCHEMA_REF,
        "schema_version": SCHEMA_VERSION,
        "generatedAt": _emit_timestamp(catalog, reproducible=reproducible),
        "catalogueVersion": _read_version(catalog.project_root),
        "build": {
            "reproducible": reproducible,
            "python": platform.python_version(),
            "platform": platform.platform() if not reproducible else "ubuntu-latest",
        },
        "counts": counts,
        "quality": quality,
        "coverage": coverage,
        "distributions": distributions,
        "ucsByCategory": by_category,
        "leaders": leaders,
    }
    return payload


# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------

def _counts(
    catalog: Catalog,
    ucs: list[tuple[Any, Any, Any]],
) -> dict[str, int]:
    """Top-level catalogue cardinality: categories, subcategories, UCs, …"""
    sub_count = sum(len(cat.get("s", [])) for cat in catalog.categories)
    return {
        "categories": len(catalog.categories),
        "subcategories": sub_count,
        "useCases": len(ucs),
        "regulations": len(catalog.regulations),
        "equipment": len(catalog.equipment),
    }


# ---------------------------------------------------------------------------
# Quality block — tier counts + depth percentiles + GE coverage
# ---------------------------------------------------------------------------

def _quality_block(
    ucs: list[tuple[Any, Any, Any]],
) -> dict[str, Any]:
    """Quality tier counts, depth-score percentiles, GE coverage."""
    tier_counts: Counter[str] = Counter()
    depth_scores: list[int] = []
    ge_lengths: list[int] = []
    ge_present_count = 0

    for _cat, _sub, uc in ucs:
        tier = uc.get("_qt") or "none"
        if tier not in _QUALITY_TIERS:
            tier = "none"
        tier_counts[tier] += 1

        depth = uc.get("_qs")
        if isinstance(depth, int):
            depth_scores.append(depth)
        elif isinstance(depth, float) and not math.isnan(depth):
            depth_scores.append(int(depth))

        ge = uc.get("ge", "")
        if isinstance(ge, str) and ge.strip():
            ge_present_count += 1
            ge_lengths.append(len(ge))

    total = max(len(ucs), 1)
    return {
        "tierCounts": {tier: int(tier_counts.get(tier, 0)) for tier in _QUALITY_TIERS},
        "tierPercentages": {
            tier: round(100.0 * tier_counts.get(tier, 0) / total, 2)
            for tier in _QUALITY_TIERS
        },
        "depthScore": _percentile_block(depth_scores),
        "grandmaExplanation": {
            "presentCount": ge_present_count,
            "presentPercentage": round(100.0 * ge_present_count / total, 2),
            "characterLength": _percentile_block(ge_lengths),
        },
    }


# ---------------------------------------------------------------------------
# Coverage block — pure presence counts on key fields.
# ---------------------------------------------------------------------------

def _coverage_block(
    ucs: list[tuple[Any, Any, Any]],
) -> dict[str, Any]:
    """How many UCs carry each cross-cutting field (compliance, MITRE, …)."""
    total = max(len(ucs), 1)
    has_regs = 0
    has_mitre = 0
    has_cim = 0
    has_equipment = 0
    has_prerequisites = 0
    is_escu = 0
    is_escu_rba = 0

    for _cat, _sub, uc in ucs:
        if uc.get("regs"):
            has_regs += 1
        if uc.get("mitre"):
            has_mitre += 1
        if uc.get("a"):  # cimModels short-key
            has_cim += 1
        if uc.get("e"):  # equipment short-key
            has_equipment += 1
        if uc.get("pre"):
            has_prerequisites += 1
        if uc.get("escu"):
            is_escu += 1
        if uc.get("escu_rba"):
            is_escu_rba += 1

    def _pct(n: int) -> float:
        return round(100.0 * n / total, 2)

    return {
        "compliance": {"count": has_regs, "percentage": _pct(has_regs)},
        "mitreAttack": {"count": has_mitre, "percentage": _pct(has_mitre)},
        "cimModels": {"count": has_cim, "percentage": _pct(has_cim)},
        "equipment": {"count": has_equipment, "percentage": _pct(has_equipment)},
        "prerequisites": {
            "count": has_prerequisites,
            "percentage": _pct(has_prerequisites),
        },
        "escuDetections": {"count": is_escu, "percentage": _pct(is_escu)},
        "escuRiskBased": {"count": is_escu_rba, "percentage": _pct(is_escu_rba)},
    }


# ---------------------------------------------------------------------------
# Categorical distributions — wave / criticality / difficulty.
# ---------------------------------------------------------------------------

def _distributions_block(
    ucs: list[tuple[Any, Any, Any]],
) -> dict[str, Any]:
    """Categorical histogram for the three tier-style facets."""
    waves: Counter[str] = Counter()
    criticality: Counter[str] = Counter()
    difficulty: Counter[str] = Counter()

    for _cat, _sub, uc in ucs:
        wv = uc.get("wv") or ""
        if isinstance(wv, str) and wv.strip().lower() in _WAVE_TIERS:
            waves[wv.strip().lower()] += 1

        cv = (uc.get("c") or "").strip()
        if cv:
            criticality[cv] += 1

        fv = (uc.get("f") or "").strip()
        if fv:
            difficulty[fv] += 1

    return {
        "wave": {tier: int(waves.get(tier, 0)) for tier in _WAVE_TIERS},
        "criticality": dict(sorted(criticality.items())),
        "difficulty": dict(sorted(difficulty.items())),
    }


# ---------------------------------------------------------------------------
# Per-category UC count (small + bounded, so safe to embed top-level).
# ---------------------------------------------------------------------------

def _ucs_by_category(catalog: Catalog) -> dict[str, int]:
    """Map ``str(catId) -> uc_count`` for every category in deterministic order.

    Sort key is the integer category id so '10' sorts after '9' even
    when serialised. JSON object key order is preserved by
    ``json.dumps(... sort_keys=True)`` because we coerce to string.
    """
    rows: list[tuple[int, str, int]] = []
    for cat in catalog.categories:
        cid = cat.get("i")
        if not isinstance(cid, int):
            continue
        n_ucs = sum(len(sub.get("u", [])) for sub in cat.get("s", []))
        rows.append((cid, str(cid), n_ucs))
    rows.sort(key=lambda r: r[0])
    return {key: count for _cid, key, count in rows}


# ---------------------------------------------------------------------------
# Top-N "leaderboards" — the single most actionable signal for stewardship.
# ---------------------------------------------------------------------------

def _leaderboards(
    ucs: list[tuple[Any, Any, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Top-N regulations, MITRE techniques, CIM models, equipment IDs."""
    regs: Counter[str] = Counter()
    mitre: Counter[str] = Counter()
    cim: Counter[str] = Counter()
    equipment: Counter[str] = Counter()

    for _cat, _sub, uc in ucs:
        for r in uc.get("regs", []) or []:
            if isinstance(r, str) and r.strip():
                regs[r.strip()] += 1
        for m in uc.get("mitre", []) or []:
            if isinstance(m, str) and m.strip():
                mitre[m.strip()] += 1
        for c in uc.get("a", []) or []:
            if isinstance(c, str) and c.strip():
                cim[c.strip()] += 1
        for e in uc.get("e", []) or []:
            if isinstance(e, str) and e.strip():
                equipment[e.strip()] += 1

    return {
        "regulations": _top_n(regs, _TOP_N_REGULATIONS, "regulation"),
        "mitreAttack": _top_n(mitre, _TOP_N_MITRE, "technique"),
        "cimModels": _top_n(cim, _TOP_N_CIM, "model"),
        "equipment": _top_n(equipment, _TOP_N_EQUIPMENT, "id"),
    }


def _top_n(counter: Counter[str], n: int, key_label: str) -> list[dict[str, Any]]:
    """Return up to ``n`` entries from ``counter`` ordered by (-count, key).

    Ties broken alphabetically so two consecutive --reproducible builds
    produce the same ordering even when underlying iteration order
    differs.
    """
    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{key_label: k, "count": v} for k, v in items[:n]]


# ---------------------------------------------------------------------------
# Percentile helper — pure, deterministic, no numpy.
# ---------------------------------------------------------------------------

def _percentile_block(values: list[int]) -> dict[str, Any]:
    """Return ``{count, min, max, mean, p50, p90, p99}`` for ``values``.

    Empty input returns zeros so the wire shape stays identical across
    builds. Mean is rounded to two decimal places; percentiles use the
    "nearest-rank" method (``ceil(p/100 * N)`` index, 1-indexed) which
    is stable, stdlib-only, and matches the convention used by
    BUILD-INFO.json's ``schemas`` block.
    """
    if not values:
        return {"count": 0, "min": 0, "max": 0, "mean": 0.0, "p50": 0, "p90": 0, "p99": 0}
    sorted_values = sorted(values)
    n = len(sorted_values)
    return {
        "count": n,
        "min": sorted_values[0],
        "max": sorted_values[-1],
        "mean": round(sum(sorted_values) / n, 2),
        "p50": _nearest_rank(sorted_values, 50),
        "p90": _nearest_rank(sorted_values, 90),
        "p99": _nearest_rank(sorted_values, 99),
    }


def _nearest_rank(sorted_values: list[int], percentile: int) -> int:
    """Nearest-rank percentile, stdlib-only.

    For percentile p (1..100): index = ceil(p/100 * N). 1-indexed; we
    convert to 0-indexed and clamp so a degenerate single-element input
    still returns the right thing.
    """
    n = len(sorted_values)
    if n == 0:
        return 0
    idx = max(1, math.ceil(percentile / 100.0 * n))
    idx = min(idx, n)
    return sorted_values[idx - 1]


# ---------------------------------------------------------------------------
# Reproducibility helpers — match build_info.py conventions.
# ---------------------------------------------------------------------------

def _emit_timestamp(catalog: Catalog, *, reproducible: bool) -> str:
    if reproducible:
        return _git_commit_iso(catalog.project_root)
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_commit_iso(project_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", "HEAD"],
            cwd=str(project_root),
            stderr=subprocess.DEVNULL,
        )
        ts = out.decode().strip()
        if ts:
            return ts
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "1970-01-01T00:00:00Z"


def _read_version(project_root: Path) -> str:
    p = project_root / "VERSION"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return "0.0.0"


__all__ = [
    "SCHEMA_REF",
    "SCHEMA_VERSION",
    "build_metrics",
    "render",
]
