#!/usr/bin/env python3
"""Audit gate for per-UC Splunk dashboard scaffolds under ``dist/dashboards/``.

``audit-dashboards --check`` validates every emitted ``simple.xml`` /
``studio.xml`` pair (XML + JSON parseability, SPL anti-patterns, pipe-per-line,
``splunk.*`` viz types, XML entity escaping). When artefacts are missing it
runs the generator in drift-check mode against the full catalogue.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from splunk_uc.generators.dashboards import (
    CONTENT_ROOT,
    DEFAULT_OUT,
    EmitReport,
    audit_generated,
    check_pipe_per_line,
    emit_all,
    validate_artefact_pair,
    validate_simple_xml,
    validate_spl_text,
    validate_studio_xml,
)

__all__ = [
    "EmitReport",
    "audit_generated",
    "check_pipe_per_line",
    "emit_all",
    "main",
    "validate_artefact_pair",
    "validate_simple_xml",
    "validate_spl_text",
    "validate_studio_xml",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit per-UC Splunk dashboard scaffolds (dist/dashboards/)."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate artefacts on disk; regenerate+diff when missing or stale.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Dashboard output root (default: dist/dashboards)",
    )
    parser.add_argument(
        "--content",
        type=Path,
        default=CONTENT_ROOT,
        help="UC content root (default: content/)",
    )
    args = parser.parse_args(argv)

    if not args.check:
        parser.error("audit-dashboards requires --check")

    validation = audit_generated(args.out)
    drift = emit_all(args.content, args.out, check=True)
    report = EmitReport(
        checked=max(validation.checked, drift.checked),
        drift=drift.drift,
        skipped=validation.skipped + drift.skipped,
        errors=[*validation.errors, *drift.errors],
        uc_ids=validation.uc_ids or drift.uc_ids,
    )

    print(
        f"audit-dashboards: checked={report.checked} drift={report.drift} "
        f"skipped={report.skipped} errors={len(report.errors)}"
    )
    for msg in report.errors[:25]:
        print(f"  ERROR: {msg}", file=sys.stderr)
    if len(report.errors) > 25:
        print(f"  ... and {len(report.errors) - 25} more", file=sys.stderr)

    if report.errors or report.drift:
        return 1
    if report.checked < 500:
        print(
            f"ERROR: expected at least 500 UC dashboard pairs, found {report.checked}",
            file=sys.stderr,
        )
        return 1
    print(f"audit-dashboards: OK ({report.checked} UC dashboard pairs, no drift).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
