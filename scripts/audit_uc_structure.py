#!/usr/bin/env python3
"""Audit use-case structure across the legacy markdown corpus AND the SSOT JSON sidecars.

Two backends, one CLI (P1 step 3, repo-overhaul plan, 2026-05-08):

* ``markdown`` — walks ``use-cases/cat-*.md`` and validates the 10
  field-name conventions that the v6 dashboard parser expects. Produces
  6,565 UCs today; this is the legacy corpus that is being burned down
  in P1 step 7.
* ``json``     — walks ``content/cat-*/UC-*.json`` (the canonical SSOT
  per ADR-0007) and validates the 13 required fields documented in
  ``AGENTS.md`` and the ``uc.schema.json`` v1.6.x contract. Produces
  7,657 UCs — covers the ~1,092 UCs that are missing from the markdown
  corpus today.

By default we run **both** backends and report issues separately so the
operator can see exactly where each gap lives. Use ``--source markdown``
or ``--source json`` to scope down. CI runs both.
"""
from __future__ import annotations

import argparse
import glob
import json as jsonlib
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USE_CASES = os.path.join(REPO_ROOT, "use-cases", "cat-*.md")
CONTENT = os.path.join(REPO_ROOT, "content", "cat-*", "UC-*.json")

LARGE_THRESHOLD = 5000
SAMPLE_SIZE = 200

VALID_CRITICALITY = frozenset(
    {"🔴 Critical", "🟠 High", "🟡 Medium", "🟢 Low"}
)
VALID_DIFFICULTY = frozenset(
    {"🟢 Beginner", "🔵 Intermediate", "🟠 Advanced", "🔴 Expert"}
)

# JSON-schema enums per ``schemas/uc.schema.json`` v1.6.x. Must stay in
# lockstep with the schema; ``tests/build/test_audit_uc_structure_json.py``
# enforces the linkage.
VALID_CRITICALITY_JSON = frozenset({"critical", "high", "medium", "low"})
VALID_DIFFICULTY_JSON = frozenset(
    {"beginner", "intermediate", "advanced", "expert"}
)

REQUIRED_FIELDS = [
    "Criticality",
    "Difficulty",
    "Monitoring type",
    "Value",
    "App/TA",
    "Data Sources",
    "SPL",
    "Implementation",
    "Visualization",
    "CIM Models",
]

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
#
# ``cimModels``: ``[]`` means "no CIM data model maps to this UC". This
# is common for cat-22 compliance UCs that report on policy artefacts
# rather than telemetry events, and for OT/IoT UCs whose semantics
# don't fit the security-leaning CIM. Markdown encodes this as
# ``- **CIM Models:** N/A``; JSON encodes it as ``"cimModels": []``.
JSON_FIELDS_ALLOW_EMPTY_LIST = frozenset({"cimModels"})

RE_UC_HEAD = re.compile(
    r"^###\s+(UC-\d+\.\d+\.\d+)\s*·\s*(.*)$", re.MULTILINE
)
RE_FIELD_LINE = re.compile(
    r"^\s*-\s*\*\*([^*]+):\*\*\s*(.*)$"
)


@dataclass
class UCParse:
    uc_id: str
    file_path: str
    title: str
    body: str
    fields: dict = field(default_factory=dict)
    spl_fenced: Optional[str] = None


def split_uc_blocks(text: str, file_path: str) -> List[UCParse]:
    matches = list(RE_UC_HEAD.finditer(text))
    if not matches:
        return []
    out: List[UCParse] = []
    for i, m in enumerate(matches):
        uc_id = m.group(1)
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        out.append(UCParse(uc_id=uc_id, file_path=file_path, title=title, body=body))
    return out


def extract_field_lines(body: str) -> dict:
    fields: dict = {}
    for line in body.splitlines():
        mm = RE_FIELD_LINE.match(line)
        if mm:
            name = mm.group(1).strip()
            val = mm.group(2).strip()
            if name not in fields:
                fields[name] = val
    return fields


RE_SPL_MARKER = re.compile(r"-\s+\*\*SPL(?:\s*\([^)]*\))?:\*\*")


def extract_spl_fenced(body: str) -> Tuple[Optional[str], str]:
    m = RE_SPL_MARKER.search(body)
    if m is None:
        return None, "no_SPL_marker"

    rest = body[m.end():]
    lines = rest.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return None, "no_fence_after_SPL"

    fence_start = lines[i].strip()
    if not fence_start.startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or not lines[i].strip().startswith("```"):
            return None, "no_opening_fence_after_SPL"
        fence_start = lines[i].strip()

    inner_lines: List[str] = []
    i += 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "```":
            return "\n".join(inner_lines), ""
        inner_lines.append(line)
        i += 1
    return None, "unclosed_fence_after_SPL"


def audit_uc(uc: UCParse) -> List[str]:
    issues: List[str] = []
    uc.fields = extract_field_lines(uc.body)
    spl_content, spl_err = extract_spl_fenced(uc.body)
    uc.spl_fenced = spl_content

    for fname in REQUIRED_FIELDS:
        if fname == "SPL":
            continue
        if fname not in uc.fields:
            issues.append(f"{uc.uc_id}: missing field **{fname}:**")
        else:
            v = uc.fields[fname].strip()
            if not v:
                issues.append(f"{uc.uc_id}: empty field **{fname}:**")

    if spl_err:
        issues.append(f"{uc.uc_id}: SPL block problem ({spl_err})")
    elif spl_content is not None:
        if not spl_content.strip():
            issues.append(f"{uc.uc_id}: SPL code block is empty")
    else:
        issues.append(f"{uc.uc_id}: could not parse SPL fenced block")

    crit = uc.fields.get("Criticality", "").strip()
    if crit and crit not in VALID_CRITICALITY:
        issues.append(
            f"{uc.uc_id}: invalid **Criticality:** {crit!r} (expected one of {sorted(VALID_CRITICALITY)})"
        )

    diff = uc.fields.get("Difficulty", "").strip()
    if diff and diff not in VALID_DIFFICULTY:
        issues.append(
            f"{uc.uc_id}: invalid **Difficulty:** {diff!r} (expected one of {sorted(VALID_DIFFICULTY)})"
        )

    return issues


def audit_uc_json(uc_path: str, payload: dict) -> List[str]:
    """Validate a single SSOT UC sidecar against the AGENTS.md contract.

    Mirrors ``audit_uc()`` for markdown but operates on the JSON shape:

    * Each entry in ``REQUIRED_JSON_FIELDS`` must be present and non-empty.
    * ``criticality`` / ``difficulty`` must use the schema enum (lower-case
      strings; the markdown emoji forms are explicitly rejected as a
      regression hint).
    * ``spl`` must be a non-empty string.
    * ``id`` must match the filename stem (UC-X.Y.Z.json).

    The error message includes the sidecar path so authors can ``cd``
    straight to the broken file.
    """
    issues: List[str] = []
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
            if crit in VALID_CRITICALITY:
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
            if diff in VALID_DIFFICULTY:
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
            issues.append(
                f"{label}: spl must be a string (got {type(spl).__name__})"
            )
        elif not spl.strip():
            issues.append(f"{label}: spl is empty")

    return issues


def _audit_markdown(args: argparse.Namespace) -> Tuple[int, int]:
    """Run the markdown corpus audit. Returns (issue_count, uc_total)."""
    paths = sorted(glob.glob(USE_CASES))
    all_ucs: List[UCParse] = []
    per_file_counts: List[Tuple[str, int]] = []

    for p in paths:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        blocks = split_uc_blocks(text, p)
        per_file_counts.append((os.path.basename(p), len(blocks)))
        all_ucs.extend(blocks)

    total = len(all_ucs)
    seed = 42
    if args.full or total <= LARGE_THRESHOLD:
        to_check = all_ucs
        sampled = False
    else:
        random.seed(seed)
        to_check = random.sample(all_ucs, min(SAMPLE_SIZE, total))
        sampled = True

    all_issues: List[str] = []
    for uc in to_check:
        all_issues.extend(audit_uc(uc))

    print("=" * 72)
    print("UC structure audit — MARKDOWN backend (use-cases/cat-*.md)")
    print("=" * 72)
    print(f"Files scanned: {len(paths)}")
    print(f"Total UC blocks parsed: {total}")
    if sampled:
        print(
            f"Sampling: {len(to_check)} UCs checked (random seed={seed}, population>{LARGE_THRESHOLD})"
        )
    elif args.full and total > LARGE_THRESHOLD:
        print(f"Full scan: all {total} UCs checked (--full, population>{LARGE_THRESHOLD})")
    else:
        print(f"All {total} UCs checked (population at or under threshold {LARGE_THRESHOLD})")
    print()
    print("UC counts per file:")
    for name, c in per_file_counts:
        print(f"  {c:5d}  {name}")
    print(f"  {'─' * 40}")
    print(f"  {total:5d}  TOTAL")
    print()
    print(f"Total markdown issues found (in checked set): {len(all_issues)}")
    print()
    if all_issues:
        print("COMPLETE MARKDOWN ISSUE LIST (checked set):")
        print("-" * 72)
        for line in all_issues:
            print(line)
    else:
        print("No markdown issues found in the checked set.")
    print()

    return len(all_issues), total


def _load_baseline(path: Optional[str]) -> set:
    """Read a known-issues baseline file. One issue line per row.

    Lines beginning with ``#`` are comments. Blank lines are ignored.
    Issues that match a baseline line are filtered out of the audit
    output and do not contribute to the failure count. As the SSOT
    migration backfills missing fields, baseline lines should be deleted
    in the same PR — never expanded.

    Returns an empty set if ``path`` is None or the file does not exist
    (CI can run without a baseline; just makes the audit stricter).
    """
    if not path:
        return set()
    if not os.path.exists(path):
        sys.stderr.write(
            f"audit_uc_structure: baseline {path!r} does not exist; "
            "ignoring.\n"
        )
        return set()
    out: set = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            out.add(line)
    return out


def _audit_json_corpus(args: argparse.Namespace) -> Tuple[int, int]:
    """Run the SSOT JSON corpus audit. Returns (issue_count, uc_total).

    Issues that match the baseline file (when ``--baseline`` is
    provided) are filtered out before the count is tallied. Use
    ``--print-baseline`` to print the current full issue list in a
    format ready to commit as a baseline; this is how the migration
    burndown is tracked.
    """
    paths = sorted(glob.glob(CONTENT))
    sidecars: List[Tuple[str, dict]] = []
    parse_errors: List[str] = []

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
                f"{rel}: top-level must be a JSON object, got "
                f"{type(payload).__name__}"
            )
            continue
        sidecars.append((p, payload))

    total = len(sidecars)
    seed = 42
    if args.full or total <= LARGE_THRESHOLD:
        to_check: Iterable[Tuple[str, dict]] = sidecars
        sampled = False
    else:
        random.seed(seed)
        to_check = random.sample(sidecars, min(SAMPLE_SIZE, total))
        sampled = True

    raw_issues: List[str] = list(parse_errors)
    for path, payload in to_check:
        raw_issues.extend(audit_uc_json(path, payload))

    baseline = _load_baseline(args.baseline)
    new_issues = [i for i in raw_issues if i not in baseline]
    fixed_baselined = sorted(baseline - set(raw_issues))

    if args.print_baseline:
        # One issue per line, sorted for stable diffs. Pipe to a file:
        #   python3 scripts/audit_uc_structure.py --source json --full \
        #     --print-baseline > data/audit-baselines/uc-structure-json.txt
        for line in sorted(set(raw_issues)):
            print(line)
        return 0, total

    print("=" * 72)
    print("UC structure audit — JSON SSOT backend (content/cat-*/UC-*.json)")
    print("=" * 72)
    print(f"Sidecars scanned: {total} (parse errors: {len(parse_errors)})")
    if baseline:
        print(f"Baseline: {len(baseline)} known issues filtered.")
    if sampled:
        print(
            f"Sampling: {len(list(to_check))} UCs checked (random seed={seed}, "
            f"population>{LARGE_THRESHOLD})"
        )
    elif args.full and total > LARGE_THRESHOLD:
        print(f"Full scan: all {total} UCs checked (--full, population>{LARGE_THRESHOLD})")
    else:
        print(f"All {total} UCs checked (population at or under threshold {LARGE_THRESHOLD})")
    print()
    print(f"Total raw JSON issues:           {len(raw_issues)}")
    print(f"Total NEW JSON issues (not in baseline): {len(new_issues)}")
    print(f"Baseline lines now FIXED (delete): {len(fixed_baselined)}")
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


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Audit UC structure across the markdown corpus AND the SSOT "
            "JSON sidecars."
        )
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="Check every UC (ignore 5000+ sampling rule)",
    )
    ap.add_argument(
        "--source",
        choices=("both", "markdown", "json"),
        default="both",
        help=(
            "Which backend to run. Default: both. 'markdown' = legacy "
            "use-cases/cat-*.md (6,565 UCs). 'json' = SSOT "
            "content/cat-*/UC-*.json (7,657 UCs)."
        ),
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
    args = ap.parse_args()
    # Empty string disables the baseline lookup (used by tests).
    if args.baseline == "":
        args.baseline = None

    # ``--print-baseline`` is a maintenance aid that emits the full raw
    # issue list on stdout. Skip the markdown audit and the SUMMARY block
    # so the output is paste-able directly into the baseline file.
    if args.print_baseline:
        if args.source not in ("both", "json"):
            sys.stderr.write(
                "audit_uc_structure: --print-baseline only applies to the "
                "JSON corpus; pass --source json (or both).\n"
            )
            return 2
        _audit_json_corpus(args)
        return 0

    md_issues = md_total = 0
    js_issues = js_total = 0

    if args.source in ("both", "markdown"):
        md_issues, md_total = _audit_markdown(args)
    if args.source in ("both", "json"):
        js_issues, js_total = _audit_json_corpus(args)

    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    if args.source in ("both", "markdown"):
        print(f"  markdown corpus: {md_total} UCs, {md_issues} issues")
    if args.source in ("both", "json"):
        print(
            f"  json     SSOT:   {js_total} UCs, {js_issues} new "
            "issues vs. baseline"
        )
    print()

    if (md_issues + js_issues) == 0:
        print("All audited UCs pass.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
