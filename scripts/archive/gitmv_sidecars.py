#!/usr/bin/env python3
"""tools.build.gitmv_sidecars — preserve per-file history of legacy sidecars.

The migration in ``tools/build/migrate_to_per_uc.py`` emits the new
canonical files at ``content/cat-NN-slug/UC-X.Y.Z.json`` from scratch.
That breaks the ``git log --follow`` history of every JSON sidecar
that already existed under ``use-cases/cat-NN/uc-X.Y.Z.json``
(1 363 files at the time of writing — almost all of cat-22 plus a
sparse handful elsewhere).

This script restores that history. For every legacy sidecar:

  1. Read the migrated canonical body that the migration script wrote
     to the destination path. This is the *merged* result (sidecar
     fields take precedence over markdown-derived fields).
  2. Remove the destination file from disk (it is currently untracked
     because the new content/ tree was never committed).
  3. ``git mv`` the legacy sidecar to the destination path. Git
     records the rename even though the destination is an untracked
     path that did not exist in the index.
  4. Overwrite the destination with the merged canonical body so the
     rename diff captures the schema change in a single commit.
  5. Stage the resulting destination file.

The script is idempotent: if the legacy sidecar is already absent
(e.g. a previous run completed), it skips the move and just stages
the destination. After this runs, ``git log --follow content/cat-22-
regulatory-compliance/UC-22.1.1.json`` resolves the file's history all
the way back to its original sidecar commit.

The categories that ship sidecars are derived dynamically from the
content tree, so the script automatically picks up any future
sidecars added under cat-NN without code changes here.

Usage::

    python3 tools/build/gitmv_sidecars.py [--dry-run]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
USE_CASES_DIR = REPO_ROOT / "use-cases"
CONTENT_DIR = REPO_ROOT / "content"


def _run_git(args: list[str], *, dry_run: bool) -> subprocess.CompletedProcess[str]:
    """Run ``git`` with the requested args. ``dry_run`` only prints."""
    cmd = ["git", *args]
    if dry_run:
        print(f"  DRY  {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _content_dir_for_cat(cat_num: str) -> Path | None:
    """Return ``content/cat-NN-<slug>/`` for the given two-digit ``cat_num``."""
    matches = sorted(CONTENT_DIR.glob(f"cat-{cat_num}-*"))
    if not matches:
        return None
    return matches[0]


def _sidecar_pairs() -> list[tuple[Path, Path]]:
    """Return ``(legacy_sidecar, target_canonical)`` pairs to rename."""
    pairs: list[tuple[Path, Path]] = []
    for cat_dir in sorted(USE_CASES_DIR.glob("cat-*")):
        if not cat_dir.is_dir():
            continue
        cat_num = cat_dir.name.split("-", 1)[1]
        # Pad single-digit category numbers (cat-1 → 01) so the slug
        # match in content/ works for both spellings the legacy tree
        # used historically.
        cat_num_padded = cat_num.zfill(2)
        dest_dir = _content_dir_for_cat(cat_num_padded)
        if dest_dir is None:
            print(
                f"  WARN no content/cat-{cat_num_padded}-* directory for "
                f"sidecars under {cat_dir.relative_to(REPO_ROOT)} — skipping",
                file=sys.stderr,
            )
            continue
        for sidecar in sorted(cat_dir.glob("uc-*.json")):
            uc_id = sidecar.stem[len("uc-") :]
            target = dest_dir / f"UC-{uc_id}.json"
            if not target.exists():
                print(
                    f"  WARN no migration target for "
                    f"{sidecar.relative_to(REPO_ROOT)} — skipping",
                    file=sys.stderr,
                )
                continue
            pairs.append((sidecar, target))
    return pairs


def _process_pair(
    sidecar: Path, target: Path, *, dry_run: bool
) -> str:
    """Process one pair. Returns one of ``'moved'``, ``'staged'``, ``'skipped'``."""
    # Capture the merged canonical body BEFORE git-mv overwrites it,
    # so we can restore it after the rename.
    merged_body = target.read_bytes()

    if not sidecar.exists():
        # Legacy sidecar already gone — script was re-run after a
        # previous pass completed for this pair. Just stage the
        # destination so any unstaged changes get recorded.
        _run_git(
            ["add", "--", str(target.relative_to(REPO_ROOT))],
            dry_run=dry_run,
        )
        return "staged"

    # ``git mv`` requires the destination to be absent (or a directory)
    # so the rename takes effect. Drop the migrated file from disk first;
    # we already have its body in memory.
    if not dry_run:
        target.unlink()

    _run_git(
        [
            "mv",
            str(sidecar.relative_to(REPO_ROOT)),
            str(target.relative_to(REPO_ROOT)),
        ],
        dry_run=dry_run,
    )

    # Restore the merged canonical body. Git will see this as an
    # in-place modification of the renamed file, which still triggers
    # rename detection on commit/log because the similarity threshold
    # (50% by default) is met — the canonical schema and sidecar schema
    # share 21 of 23 keys.
    if not dry_run:
        target.write_bytes(merged_body)
    _run_git(
        ["add", "--", str(target.relative_to(REPO_ROOT))],
        dry_run=dry_run,
    )
    return "moved"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the git commands without executing them.",
    )
    args = parser.parse_args(argv)

    if not USE_CASES_DIR.exists():
        print(f"ERROR: {USE_CASES_DIR} not found", file=sys.stderr)
        return 2
    if not CONTENT_DIR.exists():
        print(f"ERROR: {CONTENT_DIR} not found — run migrate_to_per_uc.py first", file=sys.stderr)
        return 2

    pairs = _sidecar_pairs()
    if not pairs:
        print("No sidecar pairs to process. Nothing to do.")
        return 0

    print(f"Processing {len(pairs)} sidecar(s) → content/ tree…")
    moved = staged = 0
    for sidecar, target in pairs:
        try:
            result = _process_pair(sidecar, target, dry_run=args.dry_run)
        except subprocess.CalledProcessError as exc:
            print(
                f"  FAIL {sidecar.relative_to(REPO_ROOT)} → "
                f"{target.relative_to(REPO_ROOT)}\n    stderr: {exc.stderr}",
                file=sys.stderr,
            )
            return 1
        if result == "moved":
            moved += 1
        elif result == "staged":
            staged += 1

    suffix = " (DRY RUN — nothing actually changed)" if args.dry_run else ""
    print(f"Done. {moved} renamed, {staged} re-staged{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
