#!/usr/bin/env python3
"""Backfill ``cimModels`` from legacy markdown into JSON sidecars.

Repo-overhaul plan §P1 step 5b prep (2026-05-08): the v7.0 markdown→JSON
migration script did not capture every authoring field. As a result
1,785 UCs in ``content/cat-*/UC-*.json`` have either an empty
``cimModels`` array or no ``cimModels`` field at all. This is the
single largest blocker to deleting the legacy ``build.py`` and the
project-root ``catalog.json`` / ``data.js`` / ``llms*.txt`` artefacts.

This script reads ``use-cases/cat-*.md`` and writes the missing
``cimModels`` value back into the JSON sidecar. Three flavours of
source data are handled:

1. **Real list in markdown** ("- **CIM Models:** Authentication,
   Network_Sessions") → write the parsed list into the sidecar.
2. **Explicit N/A in markdown** ("- **CIM Models:** N/A") → write ``[]``
   so the audit sees a present-but-empty array (semantically equivalent
   to "no CIM applies"; AGENTS.md treats this as curated).
3. **Markdown UC has no CIM line at all** → write ``[]`` (defensive;
   covers a small tail of ~25 UCs).

UCs that exist only in JSON (no markdown counterpart, ~430 of them)
are not touched — they need real curation. The script prints them so a
human can follow up.

The script is idempotent: running it twice produces the same output as
running it once. It re-uses the same atomic write helper as the build
pipeline so partial failures cannot corrupt a sidecar.

Usage:
  python3 scripts/backfill_cim_models.py            # dry run (default)
  python3 scripts/backfill_cim_models.py --apply    # write changes
  python3 scripts/backfill_cim_models.py --apply --only UC-11.1.14
  python3 scripts/backfill_cim_models.py --report   # print breakdown only

Exit codes: 0 = clean run, 1 = at least one error encountered.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USE_CASES = REPO_ROOT / "use-cases"
CONTENT = REPO_ROOT / "content"

_NA_VALUES = {"n/a", "na", "none", "-", "tbd"}

# CIM model normalisation. AGENTS.md and most curated sidecars use the
# Splunk-canonical CamelCase form (e.g. "Authentication", "Network_Traffic")
# whereas the markdown sometimes uses lowercase or dotted variants. We
# leave casing alone (the catalog already mixes both) but trim and
# de-duplicate.
def _split_cim(raw: str) -> list[str]:
    """Split a markdown CIM line into individual model names."""
    if not raw:
        return []
    # Drop leading "- " or "* " bullet remnants, brackets, periods.
    raw = raw.strip().rstrip(".")
    # Most CIM lines are comma-separated. A few use " / " or " and ".
    parts = re.split(r"\s*[,/]\s*|\s+and\s+", raw)
    out: list[str] = []
    seen = set()
    for part in parts:
        item = part.strip().strip(".,;").strip()
        if not item:
            continue
        if item.lower() in _NA_VALUES:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def parse_markdown_cim(use_cases: Path) -> dict[str, str | None]:
    """Index every UC in the markdown corpus → its raw CIM Models line.

    Returns a dict: ``"X.Y.Z"`` → raw markdown value, or ``None`` if the
    UC heading exists but has no CIM Models line. UCs absent from
    markdown do not appear in the dict.
    """
    md_uc_to_cim: dict[str, str | None] = {}
    for mdf in sorted(use_cases.glob("cat-*-*.md")):
        text = mdf.read_text(encoding="utf-8")
        # Each UC heading is "### UC-X.Y.Z · Title" or similar.
        parts = re.split(
            r"(?=^###\s+UC-\d+\.\d+\.\d+\b)", text, flags=re.MULTILINE
        )
        for part in parts:
            head = re.match(r"###\s+UC-(\d+\.\d+\.\d+)", part)
            if not head:
                continue
            uc_id = head.group(1)
            cim_line = re.search(
                r"\*\*\s*CIM\s*Models?\s*:?\s*\*\*\s*([^\n]+)",
                part,
                re.IGNORECASE,
            )
            md_uc_to_cim[uc_id] = (
                cim_line.group(1).strip() if cim_line else None
            )
    return md_uc_to_cim


def find_sidecars_needing_cim(content: Path) -> list[tuple[str, Path]]:
    """Return ``[(uc_id, sidecar_path), ...]`` for every JSON sidecar
    whose ``cimModels`` field is missing or empty."""
    out: list[tuple[str, Path]] = []
    for path in sorted(content.glob("cat-*/UC-*.json")):
        try:
            with path.open(encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        uc_id = payload.get("id")
        if not isinstance(uc_id, str) or not uc_id:
            continue
        cim = payload.get("cimModels")
        if cim is None:
            out.append((uc_id, path))
        elif isinstance(cim, list) and not cim:
            out.append((uc_id, path))
    return out


def _atomic_write(path: Path, payload: dict) -> None:
    """Write JSON atomically, preserving the trailing newline convention."""
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def categorise(
    needing: list[tuple[str, Path]],
    md_index: dict[str, str | None],
) -> dict[str, list[tuple[str, Path, list[str]]]]:
    """Bucket each missing UC by the source we'll use to backfill."""
    buckets: dict[str, list[tuple[str, Path, list[str]]]] = {
        "from_markdown_real": [],
        "from_markdown_na": [],
        "markdown_no_cim_line": [],
        "json_only": [],
    }
    for uc_id, path in needing:
        if uc_id not in md_index:
            buckets["json_only"].append((uc_id, path, []))
            continue
        raw = md_index[uc_id]
        if raw is None:
            buckets["markdown_no_cim_line"].append((uc_id, path, []))
            continue
        if raw.strip().lower() in _NA_VALUES:
            buckets["from_markdown_na"].append((uc_id, path, []))
            continue
        models = _split_cim(raw)
        if not models:
            # Markdown had a CIM line but it parsed to nothing (e.g. just
            # punctuation). Treat as N/A.
            buckets["from_markdown_na"].append((uc_id, path, []))
        else:
            buckets["from_markdown_real"].append((uc_id, path, models))
    return buckets


def apply_one(path: Path, models: list[str]) -> bool:
    """Update ``path`` so ``cimModels`` is present and equal to ``models``.

    Returns ``True`` if the file was modified, ``False`` if it was
    already correct (so re-runs print "noop" instead of pretending to
    write).
    """
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    existing = payload.get("cimModels")
    target = list(models)
    if isinstance(existing, list) and existing == target:
        return False
    payload["cimModels"] = target
    _atomic_write(path, payload)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Write the backfill into JSON sidecars. Without this flag the "
            "script prints what it would do and exits 0."
        ),
    )
    ap.add_argument(
        "--report",
        action="store_true",
        help="Print the per-bucket breakdown and exit (no writes).",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="UC-X.Y.Z",
        help=(
            "Limit the scope to the given UC-id(s). Pass multiple times "
            "to operate on a small batch."
        ),
    )
    ap.add_argument(
        "--bucket",
        action="append",
        default=[],
        choices=(
            "from_markdown_real",
            "from_markdown_na",
            "markdown_no_cim_line",
            "json_only",
        ),
        help=(
            "Limit scope to one or more buckets. Pass multiple times to "
            "include several. Default: all buckets. Recommended phased "
            "rollout: first run with --bucket from_markdown_real "
            "--bucket from_markdown_na --bucket markdown_no_cim_line "
            "(safe markdown-sourced backfill); then a second run with "
            "--bucket json_only after manual review."
        ),
    )
    args = ap.parse_args()

    only_ids = {oid.removeprefix("UC-").strip() for oid in args.only}

    md_index = parse_markdown_cim(USE_CASES)
    needing = find_sidecars_needing_cim(CONTENT)
    if only_ids:
        needing = [n for n in needing if n[0] in only_ids]

    buckets = categorise(needing, md_index)
    total = sum(len(b) for b in buckets.values())

    print(f"Analysed {total} sidecars with missing/empty cimModels")
    print(f"  from_markdown_real:    {len(buckets['from_markdown_real']):>5}  (back-fillable from a curated CIM line)")
    print(f"  from_markdown_na:      {len(buckets['from_markdown_na']):>5}  (curator wrote 'N/A' → cimModels=[])")
    print(f"  markdown_no_cim_line:  {len(buckets['markdown_no_cim_line']):>5}  (no source data; default to [])")
    print(f"  json_only:             {len(buckets['json_only']):>5}  (no markdown counterpart; default to [], needs curation)")

    if args.report:
        return 0

    selected_buckets = set(args.bucket) if args.bucket else set(buckets.keys())
    plan: list[tuple[str, Path, list[str], str]] = []
    for label, items in buckets.items():
        if label not in selected_buckets:
            continue
        for uc_id, path, models in items:
            plan.append((uc_id, path, models, label))

    if not plan:
        print("Nothing to do.")
        return 0

    if not args.apply:
        print()
        print("Dry run. Pass --apply to write the changes.")
        return 0

    written = 0
    skipped = 0
    errors = 0
    print()
    print("Applying...")
    for uc_id, path, models, _label in plan:
        try:
            if apply_one(path, models):
                written += 1
            else:
                skipped += 1
        except Exception as exc:  # pragma: no cover - filesystem errors
            print(f"  ERROR  {uc_id} ({path}): {exc}", file=sys.stderr)
            errors += 1

    print()
    print(f"  written: {written}")
    print(f"  noop:    {skipped}")
    print(f"  errors:  {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
