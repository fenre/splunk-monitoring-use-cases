#!/usr/bin/env python3
"""Backfill secondary curator-authored fields (``cimSpl``, ``wave``) from
the legacy ``use-cases/cat-*.md`` corpus into the SSOT JSON sidecars.

Repo-overhaul plan §P1 step 5b prep #2 (2026-05-08): closes the bulk of
the remaining field-loss gap captured in
``tests/build/test_legacy_artifacts_parity.py``::

    qs (cimSpl):  364  ← curator-authored tstats SPL
    wv (wave):    96   ← curator-authored crawl/walk/run classification

The other field losses (``_qg``, ``sapp``, ``ta_link``, ``hw``, ``e``,
``premium``) are render-time enrichment outputs, not curator data — they
are addressed by other commits (lookup improvements in
``tools/build/enrichment.py``) rather than by sidecar rewrites.

Reads from ``use-cases/cat-*.md`` for source-of-truth data.
Writes to ``content/cat-NN-slug/UC-X.Y.Z.json`` atomically (write-tmp,
fsync, rename) to avoid torn files. Dry-run by default; use ``--apply``
to commit.

Usage::

    # show what would change
    python3 scripts/backfill_secondary_fields.py --report

    # apply only the cimSpl backfill
    python3 scripts/backfill_secondary_fields.py --apply --field cimSpl

    # apply both (default)
    python3 scripts/backfill_secondary_fields.py --apply

    # operate on a single UC
    python3 scripts/backfill_secondary_fields.py --apply --only UC-1.1.23

The wave value is normalized to the SSOT enum: ``crawl``, ``walk``, or
``run`` (lower-case, no emoji). The legacy markdown form
``- **Wave:** 🐢 crawl`` becomes ``"wave": "crawl"`` in JSON.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USE_CASES = REPO_ROOT / "use-cases"
CONTENT = REPO_ROOT / "content"

# Capture the value after `- **Wave:** ` on a single line; the emoji and
# any leading whitespace before the wave word are stripped. Three valid
# values per the JSON schema enum: crawl, walk, run.
RE_WAVE = re.compile(
    r"^-\s+\*\*Wave:\*\*\s+(?:[^\w]+\s+)?(crawl|walk|run)\b",
    re.IGNORECASE | re.MULTILINE,
)

# Capture the SPL fence that follows ``- **CIM SPL:**``. We match a
# single SPL fence — multiple alt cimSPL is uncommon but the legacy
# parser also extracts the first fence only.
RE_CIM_SPL_BLOCK = re.compile(
    r"^-\s+\*\*CIM\s+SPL:\*\*\s*\n```spl\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE | re.MULTILINE,
)

VALID_WAVE = frozenset({"crawl", "walk", "run"})


@dataclass(frozen=True)
class MarkdownExtract:
    """Per-UC extraction from legacy markdown."""

    cim_spl: str | None
    wave: str | None


def parse_markdown_secondary(use_cases: Path) -> dict[str, MarkdownExtract]:
    """Return {UC-X.Y.Z: MarkdownExtract(...)} for every markdown UC."""
    out: dict[str, MarkdownExtract] = {}
    for md in sorted(use_cases.glob("cat-*.md")):
        text = md.read_text(encoding="utf-8")
        # Split into per-UC blocks on ``### UC-X.Y.Z`` headings.
        parts = re.split(r"(?=^###\s+UC-\d+\.\d+\.\d+)", text, flags=re.MULTILINE)
        for blk in parts:
            m_head = re.match(r"^###\s+(UC-\d+\.\d+\.\d+)", blk)
            if not m_head:
                continue
            uc_id = m_head.group(1)

            cim_spl: str | None = None
            m_spl = RE_CIM_SPL_BLOCK.search(blk)
            if m_spl:
                cim_spl = m_spl.group(1).strip()

            wave: str | None = None
            m_wave = RE_WAVE.search(blk)
            if m_wave:
                w = m_wave.group(1).lower()
                if w in VALID_WAVE:
                    wave = w

            out[uc_id] = MarkdownExtract(cim_spl=cim_spl, wave=wave)
    return out


def find_sidecars_with_field(content: Path, key: str) -> tuple[list[tuple[str, Path, dict]], list[tuple[str, Path, dict]]]:
    """Walk ``content/`` and split sidecars into (have, missing) for ``key``.

    "have" = key present and non-empty.
    "missing" = key absent or value falsy/empty.
    """
    have: list[tuple[str, Path, dict]] = []
    missing: list[tuple[str, Path, dict]] = []
    for cat_dir in sorted(content.glob("cat-*")):
        for fp in sorted(cat_dir.glob("UC-*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"WARN: invalid JSON in {fp}: {exc}", file=sys.stderr)
                continue
            uc_id = data.get("id") or fp.stem.replace("UC-", "")
            v = data.get(key)
            populated = bool(v) and not (isinstance(v, str) and not v.strip())
            (have if populated else missing).append((uc_id, fp, data))
    return have, missing


def _atomic_write(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, raw.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def categorise_cim_spl(
    missing: list[tuple[str, Path, dict]],
    md: dict[str, MarkdownExtract],
) -> dict[str, list[tuple[str, Path, str]]]:
    """Bucket UCs missing cimSpl by what's available in markdown."""
    buckets: dict[str, list[tuple[str, Path, str]]] = {
        "from_markdown": [],
        "no_markdown_cim_spl": [],
        "json_only": [],
    }
    for uc_id, path, _ in missing:
        key = f"UC-{uc_id}"
        m = md.get(key)
        if m is None:
            buckets["json_only"].append((uc_id, path, ""))
        elif m.cim_spl:
            buckets["from_markdown"].append((uc_id, path, m.cim_spl))
        else:
            buckets["no_markdown_cim_spl"].append((uc_id, path, ""))
    return buckets


def categorise_wave(
    missing: list[tuple[str, Path, dict]],
    md: dict[str, MarkdownExtract],
) -> dict[str, list[tuple[str, Path, str]]]:
    """Bucket UCs missing wave by what's available in markdown."""
    buckets: dict[str, list[tuple[str, Path, str]]] = {
        "from_markdown": [],
        "no_markdown_wave": [],
        "json_only": [],
    }
    for uc_id, path, _ in missing:
        key = f"UC-{uc_id}"
        m = md.get(key)
        if m is None:
            buckets["json_only"].append((uc_id, path, ""))
        elif m.wave:
            buckets["from_markdown"].append((uc_id, path, m.wave))
        else:
            buckets["no_markdown_wave"].append((uc_id, path, ""))
    return buckets


def apply_one(path: Path, key: str, value: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[key] = value
    _atomic_write(path, payload)


def _selected(uc_id: str, only: list[str]) -> bool:
    if not only:
        return True
    canonical = {x.replace("UC-", "") for x in only}
    return uc_id in canonical


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="Actually write changes; default is a dry-run.")
    ap.add_argument("--report", action="store_true",
                    help="Print the per-bucket breakdown then exit.")
    ap.add_argument("--field", action="append", default=[],
                    choices=("cimSpl", "wave"),
                    help="Restrict scope to one field. Repeatable. "
                         "Default: both fields.")
    ap.add_argument("--only", action="append", default=[],
                    metavar="UC-X.Y.Z",
                    help="Limit to specific UC ID(s). Repeatable.")
    args = ap.parse_args()

    md = parse_markdown_secondary(USE_CASES)
    print(f"Indexed {len(md)} UCs from {USE_CASES}/cat-*.md")

    fields_in_scope = args.field or ["cimSpl", "wave"]
    written_total = 0
    skipped_total = 0
    error_total = 0

    for field in fields_in_scope:
        print(f"\n=== Field: {field} ===")
        _have, missing = find_sidecars_with_field(CONTENT, field)
        missing = [m for m in missing if _selected(m[0], args.only)]
        print(f"  sidecars missing/empty {field}: {len(missing)}")

        if field == "cimSpl":
            buckets = categorise_cim_spl(missing, md)
        else:
            buckets = categorise_wave(missing, md)

        for label, items in buckets.items():
            print(f"    {label:25s} {len(items)}")

        if args.report:
            continue

        plan: list[tuple[str, Path, str]] = []
        for label, items in buckets.items():
            if label != "from_markdown":
                continue
            plan.extend(items)

        if not args.apply:
            print(f"  Dry run: would write {len(plan)} sidecars. Pass --apply to commit.")
            continue

        print(f"  Applying {field} backfill to {len(plan)} sidecars...")
        for _uc_id, path, value in plan:
            try:
                apply_one(path, field, value)
                written_total += 1
            except Exception as exc:
                print(f"  ERROR writing {path}: {exc}", file=sys.stderr)
                error_total += 1
        skipped_total += sum(
            len(items)
            for label, items in buckets.items()
            if label != "from_markdown"
        )

    if args.report:
        return 0

    if args.apply:
        print(f"\nSummary: written={written_total} skipped={skipped_total} errors={error_total}")
    else:
        print("\nDry run. Pass --apply to write the changes.")
    return 0 if error_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
