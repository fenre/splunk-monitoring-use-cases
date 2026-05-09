#!/usr/bin/env python3
"""Generate a release-over-release stewardship digest for the catalogue.

Repo-overhaul plan §P8 step 4 (2026-05-09).

Why
---

``dist/metrics.json`` is the live snapshot of catalogue health (counts,
quality, coverage, leaderboards) and ``data/metrics-history/`` is the
permanent archive of those snapshots, one per release. Neither answers
two recurring stewardship questions on its own:

1. "What changed since the last release?" The deltas (UC count, gold
   tier shifts, coverage gains, leaderboard movers) are buried inside
   two large JSON blobs that no maintainer wants to diff manually.
2. "What stewardship debt is accruing?" Sidecars age out of
   ``lastReviewed``; soft-failable audits warn but exit zero (notably
   ``audit_roadmap_consistency.py``). Both are easy to ignore until a
   release cycle pretends nothing is rotting.

This generator distils both into a single small artefact that:

* a weekly GitHub Actions workflow can post to a Discussion / open as
  a tracking issue;
* a maintainer can drop into a release notes section verbatim;
* a CI gate can lint without parsing the catalogue.

Reproducibility
---------------

The generator is deterministic given fixed inputs and a fixed
``--reference-date``. CI fixtures pass ``--reference-date 2026-05-09``
so the output never drifts on the calendar. ``generatedAt`` is also
sourced from ``--reference-date`` (fixed UTC midnight) so two runs on
different machines produce byte-identical artefacts.

Wire format
-----------

Both ``dist/stewardship-digest.json`` and ``dist/stewardship-digest.md``
are emitted. The JSON validates against
``schemas/v2/stewardship-digest.schema.json`` (gated in CI). The
markdown is a human-friendly rendering of the same data and follows
the same field names so a copy-paste into release notes preserves
identifier discoverability.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_METRICS = PROJECT_ROOT / "dist" / "metrics.json"
DEFAULT_HISTORY = PROJECT_ROOT / "data" / "metrics-history"
DEFAULT_CONTENT = PROJECT_ROOT / "content"
DEFAULT_OUT = PROJECT_ROOT / "dist"

SCHEMA_REF = "/schemas/v2/stewardship-digest.schema.json"
SCHEMA_VERSION = "1.0.0"
DEFAULT_STALE_THRESHOLD_DAYS = 180
TOP_STALE_LIMIT = 20
TOP_MOVERS_LIMIT = 10
COVERAGE_AXES = (
    "compliance",
    "mitreAttack",
    "cimModels",
    "equipment",
    "escuDetections",
    "escuRiskBased",
    "prerequisites",
)
LEADER_AXES = ("regulations", "mitreAttack", "cimModels", "equipment")
LEADER_NAME_KEYS = {
    "regulations": "regulation",
    "mitreAttack": "technique",
    "cimModels": "model",
    "equipment": "equipment",
}


# ---------------------------------------------------------------------------
# Pure helpers — exercised in isolation by the unit tests.
# ---------------------------------------------------------------------------


def _parse_iso_date(s: str | None) -> _dt.date | None:
    """Return a ``date`` parsed from ``YYYY-MM-DD`` or ``None`` on failure."""
    if not isinstance(s, str) or not s:
        return None
    try:
        return _dt.date.fromisoformat(s)
    except ValueError:
        return None


def _semver_key(version: str) -> tuple[int, ...]:
    """Sort key for semver-ish strings.

    Strips both ``-prerelease`` and ``+buildmetadata`` suffixes per
    SemVer §10. Non-numeric segments fall back to 0 so we never crash
    on a hand-edited snapshot.
    """
    base = version.split("-", 1)[0].split("+", 1)[0]
    parts: list[int] = []
    for chunk in base.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _previous_snapshot(
    history_dir: Path,
    current_version: str,
) -> dict[str, Any] | None:
    """Return the highest-versioned snapshot strictly less than ``current_version``.

    Reads every ``<semver>.json`` under ``history_dir`` (skipping
    ``index.json``) and picks the largest by ``_semver_key``. Returns
    ``None`` when no eligible snapshot exists (first release ever).
    """
    if not history_dir.is_dir():
        return None
    cur_key = _semver_key(current_version)
    best_key: tuple[int, ...] | None = None
    best_doc: dict[str, Any] | None = None
    for path in sorted(history_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ver = doc.get("catalogueVersion")
        if not isinstance(ver, str):
            continue
        ver_key = _semver_key(ver)
        if ver_key >= cur_key:
            continue
        if best_key is None or ver_key > best_key:
            best_key = ver_key
            best_doc = doc
    return best_doc


def _snapshot_counts(metrics: dict[str, Any]) -> dict[str, Any]:
    """Project the subset of metrics fields we care about for delta-tracking."""
    counts = metrics.get("counts", {}) or {}
    return {
        "version": metrics.get("catalogueVersion", "0.0.0"),
        "useCases": int(counts.get("useCases", 0)),
        "categories": int(counts.get("categories", 0)),
        "subcategories": int(counts.get("subcategories", 0)),
        "regulations": int(counts.get("regulations", 0)),
        "equipment": int(counts.get("equipment", 0)),
    }


def _quality_tiers(metrics: dict[str, Any]) -> dict[str, int]:
    """Return tier counts, defaulting absent tiers to 0 (schema requires all 4)."""
    tiers = (metrics.get("quality", {}) or {}).get("tierCounts", {}) or {}
    return {
        "gold": int(tiers.get("gold", 0)),
        "silver": int(tiers.get("silver", 0)),
        "bronze": int(tiers.get("bronze", 0)),
        "none": int(tiers.get("none", 0)),
    }


def _coverage_block(metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return coverage axes keyed by name, each with count + percentage."""
    src = metrics.get("coverage", {}) or {}
    out: dict[str, dict[str, Any]] = {}
    for axis in COVERAGE_AXES:
        entry = src.get(axis) or {}
        out[axis] = {
            "count": int(entry.get("count", 0)),
            "percentage": float(entry.get("percentage", 0.0)),
        }
    return out


def _leader_block(metrics: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Return leaderboards as ``{axis: {name: count}}`` dicts for delta diff."""
    src = metrics.get("leaders", {}) or {}
    out: dict[str, dict[str, int]] = {}
    for axis in LEADER_AXES:
        name_key = LEADER_NAME_KEYS[axis]
        entries = src.get(axis) or []
        flat: dict[str, int] = {}
        for entry in entries:
            name = entry.get(name_key)
            if isinstance(name, str) and name:
                flat[name] = int(entry.get("count", 0))
        out[axis] = flat
    return out


def _delta_dict(current: dict[str, int], previous: dict[str, int]) -> dict[str, int]:
    """Per-key signed delta (current - previous), defaulting absent keys to 0."""
    keys = set(current) | set(previous)
    return {k: int(current.get(k, 0)) - int(previous.get(k, 0)) for k in keys}


def _coverage_shifts(
    current: dict[str, dict[str, Any]],
    previous: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Build per-axis ``coverageShift`` blocks for the digest.

    When ``previous`` is ``None`` we still emit the current numbers and
    a zero delta so the schema stays happy and downstream consumers
    don't need to special-case the first-release-ever path.
    """
    out: dict[str, dict[str, Any]] = {}
    for axis in COVERAGE_AXES:
        cur = current.get(axis, {"count": 0, "percentage": 0.0})
        cur_count = int(cur.get("count", 0))
        cur_pct = float(cur.get("percentage", 0.0))
        block: dict[str, Any] = {
            "currentCount": cur_count,
            "currentPercentage": cur_pct,
            "delta": 0,
        }
        if previous is not None:
            prev = previous.get(axis, {"count": 0, "percentage": 0.0})
            prev_count = int(prev.get("count", 0))
            prev_pct = float(prev.get("percentage", 0.0))
            block["previousCount"] = prev_count
            block["previousPercentage"] = prev_pct
            block["delta"] = cur_count - prev_count
            block["percentageDelta"] = round(cur_pct - prev_pct, 2)
        out[axis] = block
    return out


def _top_movers(
    axis_current: dict[str, int],
    axis_previous: dict[str, int],
    *,
    limit: int = TOP_MOVERS_LIMIT,
) -> list[dict[str, Any]]:
    """Return up to ``limit`` movers for one leaderboard axis.

    Sorted by ``abs(delta)`` descending, then by name ascending so two
    consecutive runs against the same inputs produce byte-identical
    output. Movers with ``delta == 0`` are dropped — there is nothing
    interesting to report.
    """
    keys = set(axis_current) | set(axis_previous)
    entries: list[dict[str, Any]] = []
    for name in keys:
        cur = int(axis_current.get(name, 0))
        prev = int(axis_previous.get(name, 0))
        delta = cur - prev
        if delta == 0:
            continue
        entries.append(
            {
                "name": name,
                "currentCount": cur,
                "previousCount": prev,
                "delta": delta,
            }
        )
    entries.sort(key=lambda e: (-abs(e["delta"]), e["name"]))
    return entries[:limit]


def _all_top_movers(
    current: dict[str, dict[str, int]],
    previous: dict[str, dict[str, int]] | None,
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for axis in LEADER_AXES:
        if previous is None:
            out[axis] = []
            continue
        out[axis] = _top_movers(current.get(axis, {}), previous.get(axis, {}))
    return out


# ---------------------------------------------------------------------------
# Stale-UC detection.
# ---------------------------------------------------------------------------


def _walk_sidecars(content_dir: Path) -> list[dict[str, Any]]:
    """Yield UC sidecar JSON dicts under ``content_dir``.

    Returns a list (not a generator) so callers can reuse the result
    without paying twice for the disk walk.
    """
    if not content_dir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(content_dir.rglob("UC-*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        out.append(doc)
    return out


def _stale_use_cases(
    sidecars: list[dict[str, Any]],
    *,
    reference: _dt.date,
    threshold_days: int,
) -> dict[str, Any]:
    """Compute the staleness rollup for the digest.

    UCs whose ``lastReviewed`` parses to a date older than
    ``reference - threshold_days`` are stale. UCs missing
    ``lastReviewed`` are treated as max-stale so curators see them
    first; their ``ageDays`` is reported as the threshold + 1
    (sentinel) so the schema's non-negative-integer constraint holds.
    """
    cutoff = reference - _dt.timedelta(days=threshold_days)
    stale: list[dict[str, Any]] = []
    by_category: dict[str, int] = {}

    sentinel_age = threshold_days + 1
    for doc in sidecars:
        last_str = doc.get("lastReviewed")
        last = _parse_iso_date(last_str if isinstance(last_str, str) else None)
        if last is None:
            age_days = sentinel_age
            is_stale = True
        else:
            age_days = (reference - last).days
            is_stale = last < cutoff
        if not is_stale:
            continue
        uc_id = doc.get("id")
        title = doc.get("title")
        if not isinstance(uc_id, str) or not uc_id:
            continue
        if not isinstance(title, str) or not title:
            title = "(untitled)"
        category = uc_id.split(".", 1)[0] if "." in uc_id else "0"
        status = doc.get("status")
        if status not in ("verified", "community", "draft"):
            status = "unknown"
        stale.append(
            {
                "id": uc_id,
                "title": title,
                "category": category,
                "lastReviewed": last_str if isinstance(last_str, str) else None,
                "ageDays": int(age_days),
                "status": status,
            }
        )
        by_category[category] = by_category.get(category, 0) + 1

    stale.sort(key=lambda e: (-int(e["ageDays"]), e["id"]))
    return {
        "thresholdDays": int(threshold_days),
        "count": len(stale),
        "byCategory": dict(sorted(by_category.items(), key=lambda kv: int(kv[0]))),
        "topStale": stale[:TOP_STALE_LIMIT],
    }


# ---------------------------------------------------------------------------
# Audit-warning capture.
# ---------------------------------------------------------------------------


def _parse_audit_warnings(stderr: str, audit_name: str) -> list[dict[str, str]]:
    """Extract ``WARN :`` lines from one audit script's stderr.

    Audits like ``scripts/audit_roadmap_consistency.py`` use the
    ``WARN :`` prefix for soft-failures. Any line starting with that
    prefix becomes a warning entry; everything else is ignored. The
    function is stderr-format agnostic so we don't overfit to one
    audit's output.
    """
    out: list[dict[str, str]] = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line.startswith("WARN :"):
            continue
        message = line[len("WARN :"):].strip()
        if not message:
            continue
        out.append({"audit": audit_name, "severity": "warn", "message": message})
    return out


# ---------------------------------------------------------------------------
# Top-level digest builder.
# ---------------------------------------------------------------------------


def build_digest(
    *,
    metrics: dict[str, Any],
    previous: dict[str, Any] | None,
    sidecars: list[dict[str, Any]],
    audit_warnings: list[dict[str, str]],
    reference_date: _dt.date,
    stale_threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS,
) -> dict[str, Any]:
    """Construct the digest payload (no disk I/O)."""
    cur_counts = _snapshot_counts(metrics)
    prev_counts = _snapshot_counts(previous) if previous is not None else None

    cur_quality = _quality_tiers(metrics)
    prev_quality = _quality_tiers(previous) if previous is not None else None

    cur_coverage = _coverage_block(metrics)
    prev_coverage = _coverage_block(previous) if previous is not None else None

    cur_leaders = _leader_block(metrics)
    prev_leaders = _leader_block(previous) if previous is not None else None

    if prev_counts is not None:
        deltas = _delta_dict(
            {k: cur_counts[k] for k in cur_counts if k != "version"},
            {k: prev_counts[k] for k in prev_counts if k != "version"},
        )
    else:
        deltas = {k: 0 for k in cur_counts if k != "version"}

    if prev_quality is not None:
        quality_deltas = _delta_dict(cur_quality, prev_quality)
    else:
        quality_deltas = dict.fromkeys(cur_quality, 0)

    quality_shift = {
        "current": cur_quality,
        "previous": prev_quality,
        "deltas": quality_deltas,
    }

    stale = _stale_use_cases(
        sidecars,
        reference=reference_date,
        threshold_days=stale_threshold_days,
    )

    generated_at = _dt.datetime.combine(
        reference_date, _dt.time(0, 0, 0), tzinfo=_dt.UTC
    ).isoformat().replace("+00:00", "Z")

    return {
        "$schema": SCHEMA_REF,
        "schema_version": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "referenceDate": reference_date.isoformat(),
        "current": cur_counts,
        "previous": prev_counts,
        "deltas": {
            "useCases": deltas.get("useCases", 0),
            "categories": deltas.get("categories", 0),
            "subcategories": deltas.get("subcategories", 0),
            "regulations": deltas.get("regulations", 0),
            "equipment": deltas.get("equipment", 0),
        },
        "qualityShifts": quality_shift,
        "coverageShifts": _coverage_shifts(cur_coverage, prev_coverage),
        "topMovers": _all_top_movers(cur_leaders, prev_leaders),
        "auditWarnings": list(audit_warnings),
        "staleUseCases": stale,
    }


# ---------------------------------------------------------------------------
# Markdown rendering.
# ---------------------------------------------------------------------------


def render_markdown(digest: dict[str, Any]) -> str:
    """Render the human-readable companion to ``stewardship-digest.json``."""
    lines: list[str] = []
    lines.append("# Stewardship Digest")
    lines.append("")
    lines.append(f"_Generated {digest['generatedAt']} (reference date: {digest['referenceDate']})_")
    lines.append("")

    cur = digest["current"]
    prev = digest.get("previous")
    deltas = digest["deltas"]
    lines.append("## Catalogue counts")
    lines.append("")
    lines.append("| Field | Current | Previous | Delta |")
    lines.append("|-------|---------|----------|-------|")
    for key in ("useCases", "categories", "subcategories", "regulations", "equipment"):
        prev_val = prev.get(key) if prev else "—"
        delta_val = deltas[key]
        delta_str = "—" if prev is None else f"{delta_val:+d}"
        lines.append(f"| {key} | {cur[key]} | {prev_val} | {delta_str} |")
    lines.append("")

    quality = digest["qualityShifts"]
    lines.append("## Quality tier mix")
    lines.append("")
    lines.append("| Tier | Current | Previous | Delta |")
    lines.append("|------|---------|----------|-------|")
    for tier in ("gold", "silver", "bronze", "none"):
        prev_val = (
            quality["previous"][tier] if quality.get("previous") is not None else "—"
        )
        delta_val = quality["deltas"][tier]
        delta_str = "—" if quality.get("previous") is None else f"{delta_val:+d}"
        lines.append(f"| {tier} | {quality['current'][tier]} | {prev_val} | {delta_str} |")
    lines.append("")

    cov = digest["coverageShifts"]
    lines.append("## Coverage shifts")
    lines.append("")
    lines.append("| Axis | Count | % | Delta |")
    lines.append("|------|-------|---|-------|")
    for axis in COVERAGE_AXES:
        block = cov.get(axis, {})
        cur_count = block.get("currentCount", 0)
        cur_pct = block.get("currentPercentage", 0.0)
        delta = block.get("delta", 0)
        pct_delta = block.get("percentageDelta")
        if "previousCount" in block:
            delta_str = f"{delta:+d}"
            if pct_delta is not None:
                delta_str += f" ({pct_delta:+.2f}pp)"
        else:
            delta_str = "—"
        lines.append(f"| {axis} | {cur_count} | {cur_pct:.2f}% | {delta_str} |")
    lines.append("")

    movers = digest["topMovers"]
    for axis in LEADER_AXES:
        entries = movers.get(axis) or []
        if not entries:
            continue
        lines.append(f"## Top movers: {axis}")
        lines.append("")
        lines.append("| Name | Current | Previous | Delta |")
        lines.append("|------|---------|----------|-------|")
        for e in entries:
            lines.append(
                f"| {e['name']} | {e['currentCount']} | {e['previousCount']} |"
                f" {e['delta']:+d} |"
            )
        lines.append("")

    warnings = digest["auditWarnings"]
    if warnings:
        lines.append("## Open audit warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- **{w['audit']}** ({w['severity']}): {w['message']}")
        lines.append("")

    stale = digest["staleUseCases"]
    lines.append(
        f"## Stale use cases ({stale['count']} above {stale['thresholdDays']}-day threshold)"
    )
    lines.append("")
    if stale["topStale"]:
        lines.append("| ID | Title | Status | Last reviewed | Age (days) |")
        lines.append("|----|-------|--------|---------------|-----------|")
        for s in stale["topStale"]:
            last = s.get("lastReviewed") or "—"
            lines.append(
                f"| UC-{s['id']} | {s['title']} | {s['status']} | {last} |"
                f" {s['ageDays']} |"
            )
        lines.append("")
    else:
        lines.append("_No stale UCs above threshold — every sidecar has been reviewed recently._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI plumbing.
# ---------------------------------------------------------------------------


def _emit(out_dir: Path, digest: dict[str, Any]) -> tuple[Path, Path]:
    """Write JSON + markdown twins to ``out_dir`` and return the two paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "stewardship-digest.json"
    md_path = out_dir / "stewardship-digest.md"
    json_path.write_text(
        json.dumps(digest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(digest), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the weekly stewardship digest from dist/metrics.json"
        " and data/metrics-history/.",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=DEFAULT_METRICS,
        help="Path to dist/metrics.json (default: %(default)s).",
    )
    parser.add_argument(
        "--history-dir",
        type=Path,
        default=DEFAULT_HISTORY,
        help="Path to data/metrics-history/ (default: %(default)s).",
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=DEFAULT_CONTENT,
        help="Path to content/ (default: %(default)s).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Directory to emit stewardship-digest.{json,md} (default: %(default)s).",
    )
    parser.add_argument(
        "--reference-date",
        default=None,
        help="Override 'today' for staleness calculations (YYYY-MM-DD)."
        " When omitted we use today (UTC), which makes the artefact non-reproducible"
        " and is therefore unsuitable for CI fixtures.",
    )
    parser.add_argument(
        "--stale-threshold-days",
        type=int,
        default=DEFAULT_STALE_THRESHOLD_DAYS,
        help="Age cutoff above which a UC is considered stale (default: %(default)s).",
    )
    parser.add_argument(
        "--audit-warning",
        action="append",
        default=[],
        metavar="AUDIT_NAME=MESSAGE",
        help="Capture an open audit warning. Can be passed multiple times."
        " Format: 'audit_name=warning text'.",
    )
    args = parser.parse_args(argv)

    if not args.metrics.is_file():
        print(f"error: --metrics {args.metrics} does not exist", file=sys.stderr)
        return 2
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    cur_version = metrics.get("catalogueVersion", "0.0.0")
    previous = _previous_snapshot(args.history_dir, cur_version)
    sidecars = _walk_sidecars(args.content_dir)

    audit_warnings: list[dict[str, str]] = []
    for raw in args.audit_warning:
        if "=" not in raw:
            print(
                f"error: --audit-warning {raw!r} must be 'audit_name=message'",
                file=sys.stderr,
            )
            return 2
        name, message = raw.split("=", 1)
        name = name.strip()
        message = message.strip()
        if not name or not message:
            print(
                f"error: --audit-warning {raw!r} must be 'audit_name=message'",
                file=sys.stderr,
            )
            return 2
        audit_warnings.append({"audit": name, "severity": "warn", "message": message})

    if args.reference_date:
        ref = _parse_iso_date(args.reference_date)
        if ref is None:
            print(
                f"error: --reference-date {args.reference_date!r} not a valid YYYY-MM-DD date",
                file=sys.stderr,
            )
            return 2
    else:
        ref = _dt.datetime.now(tz=_dt.UTC).date()

    if args.stale_threshold_days < 1:
        print(
            f"error: --stale-threshold-days must be >= 1 (got {args.stale_threshold_days})",
            file=sys.stderr,
        )
        return 2

    digest = build_digest(
        metrics=metrics,
        previous=previous,
        sidecars=sidecars,
        audit_warnings=audit_warnings,
        reference_date=ref,
        stale_threshold_days=args.stale_threshold_days,
    )
    json_path, md_path = _emit(args.out, digest)
    print(f"wrote {json_path.relative_to(PROJECT_ROOT) if json_path.is_relative_to(PROJECT_ROOT) else json_path}")
    print(f"wrote {md_path.relative_to(PROJECT_ROOT) if md_path.is_relative_to(PROJECT_ROOT) else md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
