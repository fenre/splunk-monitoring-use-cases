#!/usr/bin/env python3
"""Template provenance audit — detect bulk-enricher fingerprints in UC sidecars.

Surfaces which use cases still carry script-made prose from the v8.22 gold
uplift enrichers. Consumed by hand-craft burndown planning and
``lift-validate --require-handcraft``.

Outputs ``reports/template-provenance.json`` when ``--check`` or ``--report``.

Usage:
    PYTHONPATH=src python3 -m splunk_uc audit-template-provenance
    PYTHONPATH=src python3 -m splunk_uc audit-template-provenance --check
    PYTHONPATH=src python3 -m splunk_uc audit-template-provenance --report
    PYTHONPATH=src python3 -m splunk_uc audit-template-provenance --files content/cat-01-server-compute/UC-1.1.1.json
    PYTHONPATH=src python3 -m splunk_uc audit-template-provenance --check --max-templated 12691
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from splunk_uc.audits._template_fingerprints import (
    detect_template_flags,
    infer_priority,
    is_fully_templated_v2,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_DIR = REPO_ROOT / "content"
REPORT_PATH = REPO_ROOT / "reports" / "template-provenance.json"


def _iter_uc_paths(files: list[str] | None) -> list[Path]:
    if files:
        paths: list[Path] = []
        for raw in files:
            path = Path(raw)
            if not path.is_absolute():
                path = REPO_ROOT / path
            paths.append(path)
        return sorted(paths)
    return sorted(CONTENT_DIR.rglob("UC-*.json"))


def _category_from_path(path: Path) -> str:
    try:
        rel = path.relative_to(CONTENT_DIR)
        return rel.parts[0] if rel.parts else "unknown"
    except ValueError:
        return "unknown"


def audit_paths(paths: list[Path]) -> dict[str, Any]:
    """Scan sidecars and build the template-provenance report payload."""
    flagged_entries: list[dict[str, Any]] = []
    by_category: dict[str, dict[str, int]] = {}
    flag_counts: Counter[str] = Counter()
    fully_templated = 0
    any_flag = 0
    clean = 0
    scanned = 0

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue

        scanned += 1
        try:
            rel = str(path.relative_to(REPO_ROOT))
        except ValueError:
            rel = str(path)
        uc_id = f"UC-{data.get('id', path.stem.replace('UC-', ''))}"
        flags = detect_template_flags(data)
        category = _category_from_path(path)

        if flags:
            any_flag += 1
            for flag in flags:
                flag_counts[flag] += 1
        else:
            clean += 1

        if is_fully_templated_v2(flags):
            fully_templated += 1

        cat_bucket = by_category.setdefault(
            category,
            {"total": 0, "any_template": 0, "fully_templated_v2": 0, "clean": 0},
        )
        cat_bucket["total"] += 1
        if flags:
            cat_bucket["any_template"] += 1
        else:
            cat_bucket["clean"] += 1
        if is_fully_templated_v2(flags):
            cat_bucket["fully_templated_v2"] += 1

        if flags:
            flagged_entries.append(
                {
                    "id": uc_id,
                    "file": rel,
                    "category": category,
                    "flags": flags,
                    "fully_templated_v2": is_fully_templated_v2(flags),
                    "priority": infer_priority(data, rel_path=rel),
                }
            )

    return {
        "$comment": (
            "Template provenance audit. Flags mark bulk-enricher fingerprints "
            "from scripts/enrich_gold_v*.py — not Gold audit pass/fail."
        ),
        "schema_version": "1.0",
        "summary": {
            "total": scanned,
            "any_template": any_flag,
            "fully_templated_v2": fully_templated,
            "clean": clean,
            "by_flag": dict(sorted(flag_counts.items())),
        },
        "by_category": dict(sorted(by_category.items())),
        "ucs": sorted(flagged_entries, key=lambda row: (row["priority"], row["id"])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", nargs="*", help="Specific UC JSON paths to audit")
    parser.add_argument("--check", action="store_true", help="Exit 1 when over cap flags")
    parser.add_argument(
        "--max-templated",
        type=int,
        default=None,
        help="Fail --check when fully_templated_v2 count exceeds this cap",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write reports/template-provenance.json (default with --check)",
    )
    parser.add_argument(
        "--max-any",
        type=int,
        default=None,
        help="Fail --check when any_template count exceeds this cap",
    )
    args = parser.parse_args(argv)

    paths = _iter_uc_paths(args.files)
    payload = audit_paths(paths)

    if args.report or args.check:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")

    summary = payload["summary"]
    print(
        f"Template provenance: {summary['total']} scanned, "
        f"{summary['fully_templated_v2']} fully templated v2, "
        f"{summary['any_template']} any flag, {summary['clean']} clean"
    )

    if args.check:
        if args.max_templated is not None and summary["fully_templated_v2"] > args.max_templated:
            print(
                f"FAIL: fully_templated_v2 {summary['fully_templated_v2']} "
                f"> max {args.max_templated}",
                file=sys.stderr,
            )
            return 1
        if args.max_any is not None and summary["any_template"] > args.max_any:
            print(
                f"FAIL: any_template {summary['any_template']} > max {args.max_any}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
