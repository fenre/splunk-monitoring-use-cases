"""``lift-batch`` verb — pick the next N UCs for the lift loop.

Given a category (``cat-15``) and a limit, enumerates every UC under
``content/cat-15-*/UC-*.json``, scores each against the target tier,
and writes a JSON manifest of the worst-N (or a random-N sample) for
the orchestration agent to consume.

The manifest is the contract between this CLI and the agent loop:
* ``category`` — the directory the search ranged over.
* ``target_tier`` — Silver / Gold / Gold-v2.
* ``limit`` — the requested number of UCs.
* ``selection`` — ``worst-first`` or ``random``.
* ``generated_at`` — UTC RFC3339 timestamp.
* ``ucs[]`` — each entry carries ``uc_id``, ``sidecar_path``,
  ``current_score``, and ``failing_fields``.

The verb is pure-function: no AI, no subprocess, no network — it only
reads sidecars from disk and writes one manifest to disk.

Usage::

    python -m splunk_uc lift-batch --category cat-15
    python -m splunk_uc lift-batch --category cat-15 --limit 10
    python -m splunk_uc lift-batch --category cat-15 --random --seed 42
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import sys
from pathlib import Path
from typing import Any

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    TargetTier,
    score_uc,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-batch",
        description=(
            "Pick N UCs from a category sorted by depth (worst-first by "
            "default) and emit a manifest the orchestration agent can "
            "iterate over."
        ),
    )
    parser.add_argument(
        "--category",
        required=True,
        help="Category prefix, e.g. cat-15. Matches content/<category>-*/.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Maximum number of UCs in the manifest (default 30).",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--worst-first",
        dest="selection",
        action="store_const",
        const="worst-first",
        help="Sort by current depth ascending (default).",
    )
    selection.add_argument(
        "--random",
        dest="selection",
        action="store_const",
        const="random",
        help="Override --worst-first with random sampling.",
    )
    parser.set_defaults(selection="worst-first")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Deterministic shuffle seed for --random (test mode).",
    )
    parser.add_argument(
        "--target-tier",
        default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Manifest output path. Defaults to "
            "reports/lift-batch-<UTC-TIMESTAMP>.json relative to the repo root."
        ),
    )
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help="Override the content root (for tests).",
    )
    return parser


def _resolve_category(content_root: Path, category: str) -> Path | None:
    """Find the single folder matching ``<category>-*`` under content_root.

    Returns None when the glob is empty. Raises ``RuntimeError`` when
    more than one directory matches (a healthy catalogue never has two
    sibling folders starting with the same category prefix).
    """
    matches = sorted(p for p in content_root.glob(f"{category}-*") if p.is_dir())
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(
            f"multiple category folders matched {category!r}: " + ", ".join(p.name for p in matches)
        )
    return matches[0]


def _score_all(cat_dir: Path, target_tier: TargetTier) -> tuple[list[dict[str, Any]], list[str]]:
    """Score every UC sidecar under ``cat_dir``; return (entries, warnings)."""
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for sidecar in sorted(cat_dir.glob("UC-*.json")):
        try:
            report = score_uc(sidecar, target_tier=target_tier)
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            warnings.append(f"skipped {sidecar.name}: {exc}")
            continue
        entries.append(
            {
                "uc_id": f"UC-{report.uc_id}",
                "sidecar_path": str(report.sidecar_path),
                "current_score": report.current_score,
                "failing_fields": sorted(report.failing_fields.keys()),
            }
        )
    return entries, warnings


def _default_report_path(content_root: Path) -> Path:
    """Compute the default manifest path next to the content root."""
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    return content_root.parent / "reports" / f"lift-batch-{timestamp}.json"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    target_tier = TargetTier.from_str(args.target_tier)

    try:
        cat_dir = _resolve_category(args.content_root, args.category)
    except RuntimeError as exc:
        print(f"lift-batch: {exc}", file=sys.stderr)
        return 1
    if cat_dir is None:
        print(
            f"lift-batch: no category folder matched {args.category!r} under {args.content_root}",
            file=sys.stderr,
        )
        return 1

    entries, warnings = _score_all(cat_dir, target_tier)
    if not entries:
        print(
            f"lift-batch: no UC sidecars found under {cat_dir} (or all failed to score)",
            file=sys.stderr,
        )
        return 1

    if args.selection == "random":
        rng = random.Random(args.seed)
        rng.shuffle(entries)
    else:
        entries.sort(key=lambda entry: entry["current_score"])

    ucs = entries[: args.limit]

    manifest: dict[str, Any] = {
        "category": args.category,
        "target_tier": target_tier.value,
        "limit": args.limit,
        "selection": args.selection,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "ucs": ucs,
    }
    if warnings:
        manifest["warnings"] = warnings

    report_path = (
        args.report if args.report is not None else _default_report_path(args.content_root)
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"lift-batch: wrote {report_path} ({len(ucs)} UC{'s' if len(ucs) != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
