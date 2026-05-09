"""Assert that two consecutive ``--reproducible`` builds are byte-identical.

Repo-overhaul plan §P4 (build reproducibility tracker), 2026-05-09.
Relocated to ``splunk_uc.audits.build_reproducibility`` under §P6, 2026-05-09.

Why
---

The build pipeline ships a ``--reproducible`` switch designed so that
two runs against the same git HEAD produce byte-identical ``dist/``
trees. That property is load-bearing for:

* `data/metrics-history/<VERSION>.json` snapshots (verbatim copies of
  ``dist/metrics.json`` per release).
* ``dist/integrity.json`` (sha256 of every emitted file).
* Downstream consumers that pin a release by content hash.

The contract has historically been documented but never **continuously
verified**. The "12,488 differing files" panic during P8 step 4
turned out to be cursor's autocommit advancing HEAD between runs;
once the caller pins ``SOURCE_DATE_EPOCH`` to a known commit, two
consecutive builds produce zero diffs.

This audit makes that property executable. ``dist/integrity.json``
already aggregates the sha256 of every other file in the build, so
two byte-identical ``integrity.json`` files prove the entire tree
is byte-identical.

Modes
-----

* default / ``--check`` - Run two ``--reproducible`` builds in
  isolated temp directories, compare ``integrity.json`` byte-for-byte.
  Exit 0 on match, 1 on mismatch, 2 on infrastructure failure
  (build crash, missing git, etc.).
* ``--keep`` - Don't delete the two temp build directories on exit;
  prints their paths so the maintainer can ``diff -rq`` them by hand.
* ``--first-build-only`` - Smoke-test for the CI runner: just verifies
  one build succeeds and emits ``integrity.json``. Use when the
  runner can't afford a full ~90s double-build.

Cost
----

A full build is ~43s on commodity hardware (M-series Mac, MacBook Pro
2024). Two builds + integrity comparison ~ 90-100s. Too slow for
per-PR CI; appropriate for a nightly job and a manual ``make`` target.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ``parents[3]`` resolves: build_reproducibility.py -> audits/ ->
# splunk_uc/ -> src/ -> repo root. The previous home (scripts/) was
# only one level deep so this is the only path adjustment needed.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_SCRIPT = PROJECT_ROOT / "tools" / "build" / "build.py"


def _git_commit_epoch() -> str:
    """Return the epoch of HEAD as a string.

    Matches ``tools/build/build.py:_git_commit_epoch``. Pinned so two
    consecutive audit runs against the same HEAD produce identical
    ``SOURCE_DATE_EPOCH`` values regardless of whether the caller's
    environment already had one set.
    """
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "HEAD"],
            cwd=str(PROJECT_ROOT),
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"unable to read git HEAD epoch: {exc}") from exc


def _git_head_sha() -> str:
    """Return the full sha of HEAD. Used to detect mid-audit moves."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise RuntimeError(f"unable to read git HEAD sha: {exc}") from exc


def _run_build(out_dir: Path, *, epoch: str) -> int:
    """Invoke ``tools/build/build.py --out <out_dir> --reproducible``.

    Returns the build's exit code. Stdout/stderr are forwarded so
    failures stay visible in CI logs.
    """
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = epoch
    return subprocess.call(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            "--out",
            str(out_dir),
            "--reproducible",
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
    )


def _read_integrity(out_dir: Path) -> bytes:
    """Return the raw bytes of ``out_dir/integrity.json`` or raise."""
    p = out_dir / "integrity.json"
    if not p.is_file():
        raise FileNotFoundError(f"missing {p}")
    return p.read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assert two consecutive --reproducible builds are byte-identical.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Default mode: build twice, fail on mismatch. Exit 0 on match.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the two temp build directories on exit and print their paths.",
    )
    parser.add_argument(
        "--first-build-only",
        action="store_true",
        help="Just run one build and assert integrity.json appears. Faster smoke test.",
    )
    args = parser.parse_args(argv)

    head_before = _git_head_sha()
    epoch = _git_commit_epoch()
    print(f"audit_build_reproducibility: HEAD={head_before[:12]} epoch={epoch}")

    tmp_root = Path(tempfile.mkdtemp(prefix="build-repro-"))
    out_a = tmp_root / "build-a"
    out_b = tmp_root / "build-b"
    cleanup_paths: list[Path] = [tmp_root]

    try:
        rc_a = _run_build(out_a, epoch=epoch)
        if rc_a != 0:
            print(f"FAIL: first build exited {rc_a}", file=sys.stderr)
            return 2
        try:
            integrity_a = _read_integrity(out_a)
        except FileNotFoundError as exc:
            print(f"FAIL: first build did not emit integrity.json: {exc}", file=sys.stderr)
            return 2
        print(
            f"audit_build_reproducibility: first build OK  ({len(integrity_a):,} bytes integrity)"
        )

        if args.first_build_only:
            print("audit_build_reproducibility: --first-build-only => skipping second build")
            return 0

        rc_b = _run_build(out_b, epoch=epoch)
        if rc_b != 0:
            print(f"FAIL: second build exited {rc_b}", file=sys.stderr)
            return 2
        try:
            integrity_b = _read_integrity(out_b)
        except FileNotFoundError as exc:
            print(f"FAIL: second build did not emit integrity.json: {exc}", file=sys.stderr)
            return 2

        head_after = _git_head_sha()
        if head_after != head_before:
            print(
                f"FAIL: HEAD moved during audit: {head_before[:12]} -> {head_after[:12]}",
                file=sys.stderr,
            )
            return 2

        if integrity_a != integrity_b:
            print(
                "FAIL: integrity.json differs between consecutive --reproducible builds",
                file=sys.stderr,
            )
            print(f"  build-a: {out_a}/integrity.json", file=sys.stderr)
            print(f"  build-b: {out_b}/integrity.json", file=sys.stderr)
            cleanup_paths = []
            return 1

        print(
            f"audit_build_reproducibility: PASS - two builds byte-identical "
            f"({len(integrity_a):,} bytes integrity each)"
        )
        return 0
    finally:
        if args.keep:
            print(f"\nKeeping temp builds at: {tmp_root}", file=sys.stderr)
        else:
            for p in cleanup_paths:
                try:
                    shutil.rmtree(p, ignore_errors=True)
                except OSError:
                    pass


if __name__ == "__main__":
    sys.exit(main())
