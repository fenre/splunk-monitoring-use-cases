#!/usr/bin/env python3
"""Exclusions coverage audit — surfaces UCs missing useful ``exclusions`` text.

Lane K (2026-05-19): audit-only gate for the string ``exclusions`` field
already defined in ``schemas/uc.schema.json`` (``minLength: 10``). This
module does **not** introduce an array shape or mutate sidecars — Lane N
backfills missing strings using the prioritized queue this audit emits.

Classification states
---------------------

* ``missing`` — field absent or ``null``
* ``too_short`` — present but stripped length < 10 (schema floor)
* ``bare`` — 10-79 chars by default (meets schema, likely under-described)
* ``populated`` — 80-400 chars (healthy scope statement)
* ``verbose`` — >400 chars (consider trimming)

The ``--check`` gate passes when ``(populated + verbose) / corpus_size * 100``
is at or above ``--threshold`` (default ``0`` — warn-only until Lane N
lifts coverage, then ratchet the threshold upward).

Outputs (gitignored under ``dist/audits/`` when ``--out`` is used):

* ``exclusions-coverage.json`` — machine-readable report
* ``exclusions-coverage.md`` — human backlog for maintainers
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_ROOT = REPO_ROOT / "content"

REPORT_VERSION = "1.0"
SCHEMA_MIN_LENGTH = 10
DEFAULT_MIN_LENGTH = 80
VERBOSE_MAX_LENGTH = 400

STATES = ("missing", "too_short", "bare", "populated", "verbose")
CRITICALITY_ORDER = {"high": 3, "medium": 2, "low": 1}
UC_PATH_GLOB = "cat-*/UC-*.json"


@dataclass(frozen=True)
class UcExclusionFinding:
    """One UC row in the prioritized backlog."""

    id: str
    category: int
    criticality: str
    state: str
    length: int
    path: str


@dataclass
class ExclusionsCoverageReport:
    """Aggregate coverage snapshot for the whole corpus."""

    corpus_size: int
    min_length: int
    by_state: dict[str, int] = field(default_factory=lambda: dict.fromkeys(STATES, 0))
    by_category: dict[str, dict[str, int]] = field(default_factory=dict)
    by_criticality: dict[str, dict[str, int]] = field(default_factory=dict)
    prioritized_queue: list[UcExclusionFinding] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def coverage_percent(self) -> float:
        if self.corpus_size == 0:
            return 100.0
        healthy = self.by_state.get("populated", 0) + self.by_state.get("verbose", 0)
        return round(healthy / self.corpus_size * 100.0, 2)

    def to_json_dict(self, generated: str) -> dict[str, Any]:
        return {
            "version": REPORT_VERSION,
            "generated": generated,
            "corpus_size": self.corpus_size,
            "min_length": self.min_length,
            "coverage_percent": self.coverage_percent,
            "by_state": {state: self.by_state.get(state, 0) for state in STATES},
            "by_category": {
                cat: {state: counts.get(state, 0) for state in STATES}
                for cat, counts in sorted(self.by_category.items(), key=lambda kv: int(kv[0]))
            },
            "by_criticality": {
                crit: {state: counts.get(state, 0) for state in STATES}
                for crit, counts in sorted(
                    self.by_criticality.items(),
                    key=lambda kv: CRITICALITY_ORDER.get(kv[0], 0),
                    reverse=True,
                )
            },
            "prioritized_queue": [
                {
                    "id": row.id,
                    "category": row.category,
                    "criticality": row.criticality,
                    "state": row.state,
                    "length": row.length,
                    "path": row.path,
                }
                for row in self.prioritized_queue
            ],
            "parse_errors": sorted(self.parse_errors),
        }


def load_uc(path: Path) -> dict[str, Any]:
    """Load one UC sidecar JSON object."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top-level JSON is not an object")
    return payload


def classify_exclusions(uc: dict[str, Any], *, min_length: int = DEFAULT_MIN_LENGTH) -> str:
    """Return the exclusion coverage state for one UC sidecar."""
    if "exclusions" not in uc or uc["exclusions"] is None:
        return "missing"
    raw = uc["exclusions"]
    if not isinstance(raw, str):
        return "missing"
    text = raw.strip()
    if len(text) < SCHEMA_MIN_LENGTH:
        return "too_short"
    if len(text) < min_length:
        return "bare"
    if len(text) > VERBOSE_MAX_LENGTH:
        return "verbose"
    return "populated"


def _category_from_uc(uc: dict[str, Any], path: Path) -> int:
    uid = uc.get("id")
    if isinstance(uid, str):
        match = re.match(r"^(\d+)\.", uid)
        if match:
            return int(match.group(1))
    stem = path.stem
    if stem.startswith("UC-"):
        match = re.match(r"^UC-(\d+)\.", stem)
        if match:
            return int(match.group(1))
    folder = path.parent.name
    match = re.match(r"^cat-(\d+)-", folder)
    if match:
        return int(match.group(1))
    return 0


def _criticality_from_uc(uc: dict[str, Any]) -> str:
    crit = uc.get("criticality")
    if isinstance(crit, str) and crit in CRITICALITY_ORDER:
        return crit
    return "low"


def _exclusion_length(uc: dict[str, Any]) -> int:
    raw = uc.get("exclusions")
    if raw is None or not isinstance(raw, str):
        return 0
    return len(raw.strip())


def _empty_bucket() -> dict[str, int]:
    return dict.fromkeys(STATES, 0)


def _increment(bucket: dict[str, int], state: str) -> None:
    bucket[state] = bucket.get(state, 0) + 1


def _sort_key(row: UcExclusionFinding) -> tuple[int, int, tuple[int, ...]]:
    crit_rank = CRITICALITY_ORDER.get(row.criticality, 0)
    parts = tuple(int(p) if p.isdigit() else 0 for p in row.id.removeprefix("UC-").split("."))
    return (-crit_rank, row.category, parts)


def evaluate_coverage(
    content_root: Path,
    *,
    min_length: int = DEFAULT_MIN_LENGTH,
    criticality_filter: str | None = None,
) -> ExclusionsCoverageReport:
    """Walk ``content/cat-*/UC-*.json`` and classify exclusion coverage."""
    report = ExclusionsCoverageReport(corpus_size=0, min_length=min_length)
    paths = sorted(content_root.glob(UC_PATH_GLOB))

    for path in paths:
        rel = str(path.relative_to(content_root.parent))
        try:
            uc = load_uc(path)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            report.parse_errors.append(f"{rel}: {exc}")
            continue

        uid = uc.get("id")
        if not isinstance(uid, str) or not uid:
            uid = path.stem.removeprefix("UC-")
        full_id = uid if uid.startswith("UC-") else f"UC-{uid}"

        category = _category_from_uc(uc, path)
        criticality = _criticality_from_uc(uc)
        state = classify_exclusions(uc, min_length=min_length)

        report.corpus_size += 1
        _increment(report.by_state, state)

        cat_key = str(category)
        if cat_key not in report.by_category:
            report.by_category[cat_key] = _empty_bucket()
        _increment(report.by_category[cat_key], state)

        if criticality not in report.by_criticality:
            report.by_criticality[criticality] = _empty_bucket()
        _increment(report.by_criticality[criticality], state)

        if state in {"missing", "too_short"}:
            if criticality_filter is None or criticality == criticality_filter:
                report.prioritized_queue.append(
                    UcExclusionFinding(
                        id=full_id,
                        category=category,
                        criticality=criticality,
                        state=state,
                        length=_exclusion_length(uc),
                        path=rel,
                    )
                )

    report.prioritized_queue.sort(key=_sort_key)
    return report


def _generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: ExclusionsCoverageReport, *, limit: int = 50) -> str:
    """Render a maintainer-facing backlog summary."""
    lines = [
        "# Exclusions coverage audit",
        "",
        f"Generated: {_generated_timestamp()}",
        "",
        "## Summary",
        "",
        f"- Corpus size: **{report.corpus_size}** UCs",
        f"- Healthy coverage (`populated` + `verbose`): **{report.coverage_percent:.2f}%**",
        f"- Bare minimum boundary (`--min-length`): **{report.min_length}** chars",
        "",
        "### By state",
        "",
        "| State | Count |",
        "| --- | ---: |",
    ]
    for state in STATES:
        lines.append(f"| `{state}` | {report.by_state.get(state, 0)} |")

    lines.extend(["", "## Per-category histogram", "", "| Category | missing | too_short | bare | populated | verbose |", "| ---: | ---: | ---: | ---: | ---: | ---: |"])
    for cat in sorted(report.by_category.keys(), key=int):
        counts = report.by_category[cat]
        lines.append(
            f"| {cat} | {counts.get('missing', 0)} | {counts.get('too_short', 0)} | "
            f"{counts.get('bare', 0)} | {counts.get('populated', 0)} | {counts.get('verbose', 0)} |"
        )

    backlog = report.prioritized_queue[:limit]
    lines.extend(
        [
            "",
            f"## Prioritized backlog (top {len(backlog)} missing / too-short UCs)",
            "",
            "Sorted by criticality (high first), then category, then UC id.",
            "",
            "| UC ID | Category | Criticality | State | Length | Path |",
            "| --- | ---: | --- | --- | ---: | --- |",
        ]
    )
    for row in backlog:
        lines.append(
            f"| {row.id} | {row.category} | {row.criticality} | `{row.state}` | {row.length} | `{row.path}` |"
        )
    if len(report.prioritized_queue) > limit:
        lines.append("")
        lines.append(f"_… and {len(report.prioritized_queue) - limit} more missing/too-short UCs._")

    if report.parse_errors:
        lines.extend(["", "## Parse errors", ""])
        for err in report.parse_errors[:25]:
            lines.append(f"- {err}")
        if len(report.parse_errors) > 25:
            lines.append(f"- … and {len(report.parse_errors) - 25} more")

    lines.append("")
    return "\n".join(lines)


def write_outputs(
    report: ExclusionsCoverageReport,
    out_dir: Path,
    *,
    limit: int = 50,
) -> tuple[Path, Path]:
    """Write JSON + Markdown reports under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    generated = _generated_timestamp()
    json_path = out_dir / "exclusions-coverage.json"
    md_path = out_dir / "exclusions-coverage.md"
    json_path.write_text(_canonical_json(report.to_json_dict(generated)), encoding="utf-8")
    md_path.write_text(render_markdown(report, limit=limit), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when healthy coverage is below --threshold percent.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Minimum percent of populated+verbose UCs required to pass --check (default: 0).",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=DEFAULT_MIN_LENGTH,
        dest="min_length",
        help=f"Chars required for populated state (default: {DEFAULT_MIN_LENGTH}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Directory for exclusions-coverage.{json,md} (default: dist/audits).",
    )
    parser.add_argument(
        "--criticality",
        choices=sorted(CRITICALITY_ORDER.keys()),
        default=None,
        help="Only include missing/too-short findings for this criticality tier.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Cap prioritized backlog rows in markdown output (default: 50).",
    )
    args = parser.parse_args(argv)

    if args.min_length < SCHEMA_MIN_LENGTH:
        print(
            f"ERROR: --min-length must be >= schema minimum ({SCHEMA_MIN_LENGTH})",
            file=sys.stderr,
        )
        return 2

    content_root = CONTENT_ROOT
    if not content_root.is_dir():
        print(f"ERROR: content root not found: {content_root}", file=sys.stderr)
        return 2

    report = evaluate_coverage(
        content_root,
        min_length=args.min_length,
        criticality_filter=args.criticality,
    )

    out_dir = args.out if args.out is not None else REPO_ROOT / "dist" / "audits"
    json_path, md_path = write_outputs(report, out_dir, limit=args.limit)

    healthy = report.by_state.get("populated", 0) + report.by_state.get("verbose", 0)
    print(
        f"Exclusions coverage: {healthy}/{report.corpus_size} healthy "
        f"({report.coverage_percent:.2f}%), "
        f"{len(report.prioritized_queue)} missing/too-short in queue"
    )
    print(f"Wrote {json_path.relative_to(REPO_ROOT)} and {md_path.relative_to(REPO_ROOT)}")

    if args.check and report.coverage_percent < args.threshold:
        print(
            f"FAIL: coverage {report.coverage_percent:.2f}% < threshold {args.threshold:.2f}%",
            file=sys.stderr,
        )
        return 1

    if args.check:
        print(f"OK: coverage {report.coverage_percent:.2f}% >= threshold {args.threshold:.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
