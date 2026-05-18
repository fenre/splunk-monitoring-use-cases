"""``lift-score`` verb — print depth score + gap report for one UC.

Usage:
    python -m splunk_uc lift-score UC-X.Y.Z
    python -m splunk_uc lift-score UC-X.Y.Z --json
    python -m splunk_uc lift-score UC-X.Y.Z --target-tier gold
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from splunk_uc.tools.lift._common import (
    DEFAULT_CONTENT_ROOT,
    TargetTier,
    resolve_sidecar_path,
    score_uc,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc lift-score",
        description="Print depth score + gap report for one UC.",
    )
    parser.add_argument("uc_id", help="UC identifier, e.g. UC-15.1.1")
    parser.add_argument(
        "--target-tier",
        default="silver",
        choices=["silver", "gold", "gold-v2"],
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--content-root",
        type=Path,
        default=DEFAULT_CONTENT_ROOT,
        help="Override the content root (for tests)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    sidecar = resolve_sidecar_path(args.uc_id, content_root=args.content_root)
    report = score_uc(sidecar, target_tier=TargetTier.from_str(args.target_tier))

    if args.json:
        print(json.dumps(report.to_json(), indent=2, sort_keys=True))
    else:
        print(f"UC: UC-{report.uc_id}")
        print(f"Target tier: {report.target_tier.value}")
        print(f"Current score: {report.current_score}/100")
        print("")
        if report.failing_fields:
            print("Failing fields:")
            for field, reasons in sorted(report.failing_fields.items()):
                joined = "; ".join(reasons) if isinstance(reasons, list) else str(reasons)
                print(f"  - {field}: {joined}")
        else:
            print("All rubric fields satisfy the target tier.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
