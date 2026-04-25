#!/usr/bin/env python3
"""Generate per-category quality scorecard for the use-case catalog.

Measures six quality dimensions per category and rolls them up into a
single letter grade (Gold / Silver / Bronze / Needs work) so that users
and contributors can see at a glance which areas of the catalog are
mature and which need more attention.

Dimensions
----------
1. **References coverage** — % of UCs whose ``refs`` field is non-empty.
2. **Known-false-positive coverage** — % of UCs with a populated ``kfp``.
3. **MITRE ATT&CK coverage** — % of Security-pillar UCs tagged with at
   least one ATT&CK technique ID.
4. **Last-reviewed freshness** — median days since each UC was last
   reviewed, for UCs that have a reviewed date.
5. **Provenance authority** — weighted score [0.0–1.0] computed from
   `provenance.json` (splunk-official / vendor-official / mitre-attack /
   nist-compliance contribute 1.0; threat-intel = 0.8;
   splunk-blog = 0.6; community = 0.5; unclassified = 0.3;
   contributor = 0.2).
6. **Sample coverage** — % of UCs with at least one fixture in
   ``samples/``.

Each dimension is normalised to 0–100, then averaged with dimension
weights (defined in ``DIMENSION_WEIGHTS`` below) into a composite 0–100
score.  The score maps to a letter grade.

Outputs
-------
- ``docs/scorecard.md`` — Markdown summary with per-category tables
- ``scorecard.json`` — Machine-readable rollup for dashboard / APIs
- optional ``--strict`` — exit non-zero if any category scores under 50.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
PROVENANCE_PATH = REPO_ROOT / "provenance.json"
SAMPLES_DIR = REPO_ROOT / "samples"
DOC_PATH = REPO_ROOT / "docs" / "scorecard.md"
JSON_PATH = REPO_ROOT / "scorecard.json"

PROVENANCE_WEIGHT = {
    "splunk-official": 1.00,
    "vendor-official": 1.00,
    "mitre-attack":    1.00,
    "nist-compliance": 1.00,
    "threat-intel":    0.80,
    "splunk-blog":     0.60,
    "community":       0.50,
    "unclassified":    0.30,
    "contributor":     0.20,
}

# Weights must sum to 1.0.  Design rationale:
#  - References dominates because unreferenced detections are unverifiable.
#  - Provenance-authority is next: cited, but cited from where?
#  - Freshness matters but with caveats (older, stable detections are fine).
#  - KFP coverage is a strong quality signal but hard to author.
#  - Sample coverage is aspirational (top-200 goal); weight low for now.
#  - MITRE coverage only applies to security UCs; weighted modestly.
DIMENSION_WEIGHTS = {
    "content_depth":         0.20,
    "references_pct":        0.20,
    "provenance_authority":  0.20,
    "freshness":             0.15,
    "kfp_pct":               0.10,
    "mitre_pct":             0.08,
    "samples_pct":           0.07,
}
assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9


@dataclass
class CategoryScore:
    cat_num: str
    name: str
    uc_count: int
    security_count: int
    content_depth: float  # 0-100 avg depth score from Gold Standard audit
    references_pct: float
    kfp_pct: float
    mitre_pct: float
    freshness_score: float  # 0-100 where 100 = reviewed today
    freshness_median_days: float | None
    provenance_authority: float  # 0-100
    samples_pct: float
    depth_tier_distribution: dict = field(default_factory=dict)
    composite: float = 0.0
    grade: str = ""
    status_distribution: dict = field(default_factory=dict)
    origin_distribution: dict = field(default_factory=dict)


def _reviewed_days_ago(reviewed: str | None) -> int | None:
    if not reviewed:
        return None
    try:
        d = date.fromisoformat(reviewed.strip())
    except Exception:
        try:
            d = datetime.strptime(reviewed.strip(), "%Y-%m-%d").date()
        except Exception:
            return None
    delta = (_reproducible_today() - d).days
    if delta < 0:
        # Future-dated review (e.g. auto-generated placeholders); treat as fresh.
        return 0
    return delta


def _freshness_score_for_days(days: int | None) -> float:
    """Map days-since-review → 0..100 (lower is better)."""
    if days is None:
        return 0.0  # no review date at all
    if days <= 90:
        return 100.0
    if days <= 180:
        return 85.0
    if days <= 365:
        return 65.0
    if days <= 730:
        return 40.0
    return 20.0


def _load_samples_coverage() -> set[str]:
    """Return the set of UC IDs that have a sample-event fixture."""
    out: set[str] = set()
    if not SAMPLES_DIR.exists():
        return out
    for p in SAMPLES_DIR.glob("UC-*"):
        if p.is_dir():
            out.add(p.name.replace("UC-", "", 1))
    return out


def _grade(composite: float) -> str:
    if composite >= 85:
        return "Gold"
    if composite >= 70:
        return "Silver"
    if composite >= 55:
        return "Bronze"
    return "Needs work"


def _grade_badge(grade: str) -> str:
    return {
        "Gold":       "Gold",
        "Silver":     "Silver",
        "Bronze":     "Bronze",
        "Needs work": "Needs work",
    }.get(grade, grade)


def _compute_category(cat_entry: dict, provenance: dict, samples: set[str]) -> CategoryScore:
    cat_num = str(cat_entry.get("i", ""))
    name = cat_entry.get("n") or f"Category {cat_num}"
    ucs: list[dict] = []
    for sc in cat_entry.get("s", []):
        ucs.extend(sc.get("u", []))

    total = len(ucs)
    if total == 0:
        return CategoryScore(cat_num=cat_num, name=name, uc_count=0,
                             security_count=0, content_depth=0.0,
                             references_pct=0.0,
                             kfp_pct=0.0, mitre_pct=0.0, freshness_score=0.0,
                             freshness_median_days=None,
                             provenance_authority=0.0, samples_pct=0.0)

    with_refs = sum(1 for u in ucs if (u.get("refs") or "").strip())
    with_kfp  = sum(1 for u in ucs if (u.get("kfp") or "").strip())

    # MITRE coverage only for security UCs
    security_ucs = [u for u in ucs if (u.get("pillar") in ("security", "both"))]
    mitre_hits = sum(1 for u in security_ucs
                     if isinstance(u.get("mitre"), list) and len(u["mitre"]) > 0)

    # Freshness
    days_list = []
    for u in ucs:
        d = _reviewed_days_ago(u.get("reviewed"))
        if d is not None:
            days_list.append(d)
    if days_list:
        med_days = float(median(days_list))
        fresh_pct = _freshness_score_for_days(int(med_days))
    else:
        med_days = None
        fresh_pct = 0.0

    # Provenance authority
    auth_sum = 0.0
    origin_counts: dict[str, int] = defaultdict(int)
    status_counts: dict[str, int] = defaultdict(int)
    for u in ucs:
        uc_id = u.get("i") or ""
        p_entry = provenance.get("entries", {}).get(uc_id) or {}
        origin = p_entry.get("origin") or "contributor"
        origin_counts[origin] += 1
        auth_sum += PROVENANCE_WEIGHT.get(origin, 0.2)
        stat = (u.get("status") or "unset").lower()
        status_counts[stat] += 1
    provenance_authority = (auth_sum / total) * 100 if total else 0.0

    samples_hits = sum(1 for u in ucs if (u.get("i") or "") in samples)

    # Content depth from Gold Standard quality scores (injected by build)
    depth_scores = [u.get("_qs", 0) for u in ucs]
    content_depth = sum(depth_scores) / total if total else 0.0
    depth_tier_dist: dict[str, int] = defaultdict(int)
    for u in ucs:
        depth_tier_dist[u.get("_qt", "none")] += 1

    refs_pct = with_refs / total * 100
    kfp_pct  = with_kfp / total * 100
    mitre_pct = (mitre_hits / len(security_ucs) * 100) if security_ucs else 0.0
    samples_pct = samples_hits / total * 100 if total else 0.0

    composite = (
        content_depth        * DIMENSION_WEIGHTS["content_depth"] +
        refs_pct             * DIMENSION_WEIGHTS["references_pct"] +
        provenance_authority * DIMENSION_WEIGHTS["provenance_authority"] +
        fresh_pct            * DIMENSION_WEIGHTS["freshness"] +
        kfp_pct              * DIMENSION_WEIGHTS["kfp_pct"] +
        mitre_pct            * DIMENSION_WEIGHTS["mitre_pct"] +
        samples_pct          * DIMENSION_WEIGHTS["samples_pct"]
    )

    return CategoryScore(
        cat_num=cat_num,
        name=name,
        uc_count=total,
        security_count=len(security_ucs),
        content_depth=content_depth,
        references_pct=refs_pct,
        kfp_pct=kfp_pct,
        mitre_pct=mitre_pct,
        freshness_score=fresh_pct,
        freshness_median_days=med_days,
        provenance_authority=provenance_authority,
        samples_pct=samples_pct,
        depth_tier_distribution=dict(depth_tier_dist),
        composite=composite,
        grade=_grade(composite),
        status_distribution=dict(status_counts),
        origin_distribution=dict(origin_counts),
    )


def render_markdown(scores: list[CategoryScore]) -> str:
    def fmt_pct(x: float) -> str:
        return f"{x:.1f}%"

    def fmt_days(d: float | None) -> str:
        return "—" if d is None else f"{int(d)}d"

    # Global rollup
    total_ucs = sum(s.uc_count for s in scores)
    weighted_composite = (
        sum(s.composite * s.uc_count for s in scores) / total_ucs
    ) if total_ucs else 0.0

    lines = [
        "# Catalog quality scorecard",
        "",
        "Auto-generated by `scripts/generate_scorecard.py`. Do not edit by hand.",
        "",
        "## Methodology",
        "",
        "Six dimensions are measured per category, normalised to 0–100, and",
        "averaged with the following weights:",
        "",
        "| Dimension | Weight | What it measures |",
        "| --------- | ------ | ---------------- |",
        "| Content depth | 20% | Average Gold Standard depth score (0–100) measuring operational completeness |",
        "| References | 20% | % of UCs citing at least one external source |",
        "| Provenance authority | 20% | Weighted average authority of citations (Splunk official = 1.0, community = 0.5, contributor = 0.2) |",
        "| Freshness | 15% | Median age of the `Last reviewed` field (≤90d = 100, >2y = 20) |",
        "| Known false positives | 10% | % of UCs with populated KFP guidance |",
        "| MITRE ATT&CK coverage | 8% | % of security UCs tagged with ATT&CK technique IDs |",
        "| Sample fixtures | 7% | % of UCs with a `samples/UC-<id>/` fixture |",
        "",
        "Grades:",
        "",
        "| Grade | Composite | Meaning |",
        "| ----- | --------- | ------- |",
        "| **Gold** | ≥ 85 | Production-ready, well-cited, well-documented |",
        "| **Silver** | 70–84 | Solid content, minor gaps (e.g. KFP sparse) |",
        "| **Bronze** | 55–69 | Usable but needs attention (reviews overdue, light citations) |",
        "| **Needs work** | < 55 | Requires authoring effort before relying on it |",
        "",
        "## Global rollup",
        "",
        f"- **Total UCs:** {total_ucs:,}",
        f"- **Weighted composite score:** {weighted_composite:.1f} — overall grade **{_grade(weighted_composite)}**",
        "",
        "## Per-category scorecard",
        "",
        "| Cat | Category | UCs | Depth | Refs | KFP | MITRE* | Fresh | Prov. | Samples | Composite | Grade |",
        "| --- | -------- | --- | ----- | ---- | --- | ------ | ----- | ----- | ------- | --------- | ----- |",
    ]
    sorted_scores = sorted(scores,
                           key=lambda s: (int(s.cat_num) if s.cat_num.isdigit() else 9999))
    for s in sorted_scores:
        mitre_cell = f"{s.mitre_pct:.0f}%" if s.security_count else "n/a"
        lines.append(
            f"| {s.cat_num} | {s.name[:45]} | {s.uc_count:,} | "
            f"{s.content_depth:.0f} | "
            f"{fmt_pct(s.references_pct)} | {fmt_pct(s.kfp_pct)} | {mitre_cell} | "
            f"{fmt_days(s.freshness_median_days)} | {s.provenance_authority:.0f} | "
            f"{fmt_pct(s.samples_pct)} | **{s.composite:.1f}** | **{_grade_badge(s.grade)}** |"
        )
    lines.extend([
        "",
        "\\* MITRE coverage counts only UCs whose `pillar` is `security` or `both`.",
        "",
        "## Grade distribution",
        "",
        "| Grade | Categories | Total UCs |",
        "| ----- | ---------- | --------- |",
    ])
    grade_group: dict[str, list[CategoryScore]] = defaultdict(list)
    for s in scores:
        grade_group[s.grade].append(s)
    for grade in ("Gold", "Silver", "Bronze", "Needs work"):
        grp = grade_group.get(grade, [])
        ucs = sum(s.uc_count for s in grp)
        lines.append(f"| **{grade}** | {len(grp)} | {ucs:,} |")

    lines.extend([
        "",
        "## How to improve a score",
        "",
        "- **Low refs %**: add citations to `References:` using the official Splunk / vendor docs already referenced by sibling UCs.",
        "- **Low KFP %**: add a `Known false positives` section — usually 1–2 sentences describing the most common benign trigger.",
        "- **Stale freshness**: touch the `Last reviewed` field after a quick sanity check of the SPL; update when Splunk / vendor APIs change.",
        "- **Low provenance authority**: swap community blog links for the upstream official doc where available.",
        "- **Low MITRE %**: tag security UCs with the ATT&CK technique ID they detect (T1078, T1059, etc.).",
        "- **Low sample coverage**: add a fixture under `samples/UC-<id>/` — see `samples/README.md` for the schema.",
        "",
    ])
    return "\n".join(lines)


def _reproducible_now() -> str:
    """Return a UTC timestamp pinned to SOURCE_DATE_EPOCH when set.

    Honors the reproducible-builds standard env var so that
    ``tools/build/build.py --reproducible`` produces byte-identical
    scorecards across consecutive builds. Falls back to the real wall
    clock when the env var is missing (interactive runs).
    """
    import os
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _reproducible_today() -> date:
    """Return today's UTC date pinned to SOURCE_DATE_EPOCH when set.

    Used for freshness scoring so freshness ages are stable across two
    consecutive builds of the same source SHA.
    """
    import os
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).date()
    return date.today()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any category scores below 50.")
    parser.add_argument("--no-write", action="store_true",
                        help="Do not write outputs (dry-run).")
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print("catalog.json missing — run build.py first.", file=sys.stderr)
        return 2

    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        cat = json.load(fh)
    provenance: dict = {}
    if PROVENANCE_PATH.exists():
        with PROVENANCE_PATH.open("r", encoding="utf-8") as fh:
            provenance = json.load(fh)
    else:
        print("warning: provenance.json missing — provenance dimension will default to 'contributor'",
              file=sys.stderr)
        provenance = {"entries": {}}

    samples = _load_samples_coverage()

    scores: list[CategoryScore] = []
    for cat_entry in cat.get("DATA", []):
        scores.append(_compute_category(cat_entry, provenance, samples))

    if not args.no_write:
        DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOC_PATH.write_text(render_markdown(scores), "utf-8")
        print(f"Wrote {DOC_PATH}")

        JSON_PATH.write_text(
            json.dumps({
                "schema_version": 1,
                "generated_at": _reproducible_now(),
                "dimension_weights": DIMENSION_WEIGHTS,
                "categories": [
                    {
                        "cat_num": s.cat_num,
                        "name": s.name,
                        "uc_count": s.uc_count,
                        "security_count": s.security_count,
                        "content_depth": round(s.content_depth, 2),
                        "references_pct": round(s.references_pct, 2),
                        "kfp_pct": round(s.kfp_pct, 2),
                        "mitre_pct": round(s.mitre_pct, 2),
                        "freshness_score": round(s.freshness_score, 2),
                        "freshness_median_days": s.freshness_median_days,
                        "provenance_authority": round(s.provenance_authority, 2),
                        "samples_pct": round(s.samples_pct, 2),
                        "depth_tier_distribution": s.depth_tier_distribution,
                        "composite": round(s.composite, 2),
                        "grade": s.grade,
                        "status_distribution": s.status_distribution,
                        "origin_distribution": s.origin_distribution,
                    }
                    for s in scores
                ],
            }, indent=2),
            "utf-8",
        )
        print(f"Wrote {JSON_PATH}")

    # Console summary
    print("Per-category composite scores:")
    for s in sorted(scores, key=lambda s: -s.composite):
        print(f"  {s.cat_num:>4}  {s.grade:<11}  {s.composite:>5.1f}  {s.name}")

    low = [s for s in scores if s.composite < 50]
    if args.strict and low:
        print(f"\nERROR: {len(low)} categories scored below 50:", file=sys.stderr)
        for s in low:
            print(f"  cat {s.cat_num} — {s.composite:.1f} ({s.name})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
