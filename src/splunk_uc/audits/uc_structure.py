#!/usr/bin/env python3
"""Audit use-case structure across the SSOT JSON sidecars.

Walks ``content/cat-*/UC-*.json`` (the canonical SSOT per ADR-0007) and
validates the 13 required fields documented in ``AGENTS.md`` and the
``uc.schema.json`` v1.6.x contract.

Pre-v8.2.0 this audit also walked the legacy markdown corpus
(``use-cases/cat-*.md``). That corpus was deleted in v8.2.0 (see
``docs/migration-status.md``) — the JSON SSOT is now the only backend.
"""

from __future__ import annotations

import argparse
import glob
import json as jsonlib
import os
import random
import sys
from collections.abc import Iterable
from typing import Any

REPO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)),
        ),
    ),
)
CONTENT = os.path.join(REPO_ROOT, "content", "cat-*", "UC-*.json")

LARGE_THRESHOLD = 5000
SAMPLE_SIZE = 200

# JSON-schema enums per ``schemas/uc.schema.json`` v1.6.x. Must stay in
# lockstep with the schema; ``tests/build/test_audit_uc_structure_json.py``
# enforces the linkage.
VALID_CRITICALITY_JSON = frozenset({"critical", "high", "medium", "low"})
VALID_DIFFICULTY_JSON = frozenset({"beginner", "intermediate", "advanced", "expert"})

# Legacy markdown emoji forms — flagged as a regression hint when they
# accidentally land in the JSON SSOT (e.g. someone copy-pastes from an
# old report).
LEGACY_MARKDOWN_CRITICALITY = frozenset({"🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"})
LEGACY_MARKDOWN_DIFFICULTY = frozenset(
    {"🟢 Beginner", "🔵 Intermediate", "🟠 Advanced", "🔴 Expert"}
)

# AGENTS.md authoring contract — every UC sidecar must carry these keys
# with non-empty values. Tracks the 13-field practical contract that is
# stricter than the JSON schema's two-required-keys minimum (the schema
# stays loose to allow stub UCs during authoring).
REQUIRED_JSON_FIELDS = [
    "id",
    "title",
    "criticality",
    "difficulty",
    "monitoringType",
    "value",
    "app",
    "dataSources",
    "spl",
    "implementation",
    "visualization",
    "cimModels",
    "grandmaExplanation",
]

# Required fields where an empty array is a valid curation outcome
# (the curator decided "no value applies"). The field key must still
# be present, and ``null`` is still rejected, but ``[]`` is allowed.
JSON_FIELDS_ALLOW_EMPTY_LIST = frozenset({"cimModels"})


def audit_uc_json(uc_path: str, payload: dict[str, Any]) -> list[str]:
    """Validate a single SSOT UC sidecar against the AGENTS.md contract.

    * Each entry in ``REQUIRED_JSON_FIELDS`` must be present and non-empty.
    * ``criticality`` / ``difficulty`` must use the schema enum (lower-case
      strings; the markdown emoji forms are explicitly rejected as a
      regression hint).
    * ``spl`` must be a non-empty string.
    * ``id`` must match the filename stem (UC-X.Y.Z.json).
    """
    issues: list[str] = []
    rel = os.path.relpath(uc_path, REPO_ROOT)
    uc_id = payload.get("id", "<unknown>")
    label = f"{uc_id} ({rel})"

    expected_id = os.path.basename(uc_path).replace("UC-", "").replace(".json", "")
    if uc_id != expected_id:
        issues.append(
            f"{label}: id field {uc_id!r} does not match filename "
            f"({expected_id!r}); rename the file or fix the JSON."
        )

    for fname in REQUIRED_JSON_FIELDS:
        if fname not in payload:
            issues.append(f"{label}: missing required field {fname!r}")
            continue
        v = payload[fname]
        if isinstance(v, str) and not v.strip():
            issues.append(f"{label}: empty required field {fname!r}")
        elif isinstance(v, list) and not v:
            if fname not in JSON_FIELDS_ALLOW_EMPTY_LIST:
                issues.append(f"{label}: empty required field {fname!r}")
        elif v is None:
            issues.append(f"{label}: null required field {fname!r}")

    crit = payload.get("criticality", "")
    if isinstance(crit, str) and crit:
        if crit not in VALID_CRITICALITY_JSON:
            if crit in LEGACY_MARKDOWN_CRITICALITY:
                issues.append(
                    f"{label}: criticality {crit!r} uses the legacy markdown "
                    f"emoji form; SSOT requires the schema enum (e.g. "
                    f"{sorted(VALID_CRITICALITY_JSON)})."
                )
            else:
                issues.append(
                    f"{label}: invalid criticality {crit!r} "
                    f"(expected {sorted(VALID_CRITICALITY_JSON)})"
                )

    diff = payload.get("difficulty", "")
    if isinstance(diff, str) and diff:
        if diff not in VALID_DIFFICULTY_JSON:
            if diff in LEGACY_MARKDOWN_DIFFICULTY:
                issues.append(
                    f"{label}: difficulty {diff!r} uses the legacy markdown "
                    f"emoji form; SSOT requires the schema enum (e.g. "
                    f"{sorted(VALID_DIFFICULTY_JSON)})."
                )
            else:
                issues.append(
                    f"{label}: invalid difficulty {diff!r} "
                    f"(expected {sorted(VALID_DIFFICULTY_JSON)})"
                )

    spl = payload.get("spl")
    if spl is not None:
        if not isinstance(spl, str):
            issues.append(f"{label}: spl must be a string (got {type(spl).__name__})")
        elif not spl.strip():
            issues.append(f"{label}: spl is empty")

    return issues


def _load_baseline(path: str | None) -> set[str]:
    """Read a known-issues baseline file. One issue line per row.

    Lines beginning with ``#`` are comments. Blank lines are ignored.
    Issues that match a baseline line are filtered out of the audit
    output and do not contribute to the failure count. As authors fix
    UCs, baseline lines should be deleted in the same PR — never
    expanded.

    Returns an empty set if ``path`` is None or the file does not exist
    (CI can run without a baseline; just makes the audit stricter).
    """
    if not path:
        return set()
    if not os.path.exists(path):
        sys.stderr.write(f"audit_uc_structure: baseline {path!r} does not exist; ignoring.\n")
        return set()
    out: set[str] = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            out.add(line)
    return out


def _audit_json_corpus(args: argparse.Namespace) -> tuple[int, int]:
    """Run the SSOT JSON corpus audit. Returns (issue_count, uc_total)."""
    paths = sorted(glob.glob(CONTENT))
    sidecars: list[tuple[str, dict[str, Any]]] = []
    parse_errors: list[str] = []

    for p in paths:
        try:
            with open(p, encoding="utf-8") as fh:
                payload = jsonlib.load(fh)
        except (OSError, jsonlib.JSONDecodeError) as exc:
            rel = os.path.relpath(p, REPO_ROOT)
            parse_errors.append(f"{rel}: failed to parse ({exc})")
            continue
        if not isinstance(payload, dict):
            rel = os.path.relpath(p, REPO_ROOT)
            parse_errors.append(
                f"{rel}: top-level must be a JSON object, got {type(payload).__name__}"
            )
            continue
        sidecars.append((p, payload))

    total = len(sidecars)
    seed = 42
    if args.full or total <= LARGE_THRESHOLD:
        to_check: Iterable[tuple[str, dict[str, Any]]] = sidecars
        sampled = False
    else:
        random.seed(seed)
        to_check = random.sample(sidecars, min(SAMPLE_SIZE, total))
        sampled = True

    raw_issues: list[str] = list(parse_errors)
    for path, payload in to_check:
        raw_issues.extend(audit_uc_json(path, payload))

    baseline = _load_baseline(args.baseline)
    new_issues = [i for i in raw_issues if i not in baseline]
    fixed_baselined = sorted(baseline - set(raw_issues))

    if args.print_baseline:
        for line in sorted(set(raw_issues)):
            print(line)
        return 0, total

    print("=" * 72)
    print("UC structure audit — JSON SSOT (content/cat-*/UC-*.json)")
    print("=" * 72)
    print(f"Sidecars scanned: {total} (parse errors: {len(parse_errors)})")
    if baseline:
        print(f"Baseline: {len(baseline)} known issues filtered.")
    if sampled:
        print(
            f"Sampling: {SAMPLE_SIZE} UCs checked (random seed={seed}, "
            f"population>{LARGE_THRESHOLD})"
        )
    elif args.full and total > LARGE_THRESHOLD:
        print(f"Full scan: all {total} UCs checked (--full, population>{LARGE_THRESHOLD})")
    else:
        print(f"All {total} UCs checked (population at or under threshold {LARGE_THRESHOLD})")
    print()
    print(f"Total raw JSON issues:                   {len(raw_issues)}")
    print(f"Total NEW JSON issues (not in baseline): {len(new_issues)}")
    print(f"Baseline lines now FIXED (delete):       {len(fixed_baselined)}")
    print()
    if new_issues:
        print("NEW JSON ISSUES (must fix or add to baseline):")
        print("-" * 72)
        for line in new_issues:
            print(line)
        print()
    if fixed_baselined:
        print("FIXED BASELINE LINES (delete from baseline file):")
        print("-" * 72)
        for line in fixed_baselined:
            print(line)
        print()
    if not new_issues and not fixed_baselined:
        print("No JSON issues vs. baseline.")
    print()

    return len(new_issues), total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Audit UC structure across the SSOT JSON sidecars.",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="Check every UC (ignore 5000+ sampling rule)",
    )
    ap.add_argument(
        "--baseline",
        default=os.path.join(REPO_ROOT, "data", "audit-baselines", "uc-structure-json.txt"),
        help=(
            "Path to a known-issues baseline file. Issues that match a "
            "line in this file are filtered out and do not fail the "
            "audit. Pass '' (empty string) to disable baseline filtering. "
            "Default: data/audit-baselines/uc-structure-json.txt."
        ),
    )
    ap.add_argument(
        "--print-baseline",
        action="store_true",
        help=(
            "Print the full raw issue list (sorted, one per line) to "
            "stdout and exit 0. Used to refresh the baseline file when "
            "intentionally accepting new known issues."
        ),
    )
    args = ap.parse_args(argv)
    if args.baseline == "":
        args.baseline = None

    if args.print_baseline:
        _audit_json_corpus(args)
        return 0

    js_issues, js_total = _audit_json_corpus(args)

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  json SSOT: {js_total} UCs, {js_issues} new issues vs. baseline")
    print()

    if js_issues == 0:
        print("All audited UCs pass.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
