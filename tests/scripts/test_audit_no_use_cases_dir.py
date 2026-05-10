"""Unit tests for ``src/splunk_uc/audits/no_use_cases_dir.py``.

The legacy ``use-cases/`` markdown corpus was retired in v8.2.0
(see ``docs/migration-status.md``). This audit is the structural guard
rail that prevents the dual-content mess from reappearing. The tests
in this module pin its two invariants:

1. **Live repo passes.** Running the audit against the actual
   workspace must exit ``0``. If it goes red the maintainer has
   either re-introduced ``use-cases/`` somewhere or the allowlist is
   stale — both are issues we want CI to surface immediately.
2. **Negative cases trip the guard.** We synthesise a temporary repo
   on disk and verify the audit:

   * Hard-fails when ``use-cases/`` exists as a directory.
   * Hard-fails when a non-allowlisted file gains a ``use-cases/``
     path reference.
   * Allows non-repo external URLs (e.g. ``tetragon.io/docs/use-cases/``)
     so legitimate third-party links never fail the gate.
   * Allows the repo URL ``splunk-monitoring-use-cases`` so links to
     the GitHub Pages site or the source tree never fail the gate.
   * Allows files on the historical-reference allowlist.
   * Honours the ``--list-allowlist`` flag for reviewer ergonomics.

The synthetic-repo tests work by monkey-patching the module-level
``REPO_ROOT`` constant rather than re-importing the module, so the
behaviour matches what real CI invocations exercise.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

import splunk_uc.audits.no_use_cases_dir as guard

REPO_ROOT = Path(__file__).resolve().parents[2]


@contextlib.contextmanager
def _synthetic_repo(tmp_path: Path) -> Iterator[Path]:
    """Create a tiny git repo and point the guard at it."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@x",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=tmp_path,
        check=True,
    )
    original = guard.REPO_ROOT
    guard.REPO_ROOT = tmp_path
    try:
        yield tmp_path
    finally:
        guard.REPO_ROOT = original


def _git_add_all_and_commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=t@x",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )


# ──────────────────────────────────────────────────────────────────────
# Live-repo invariant: the audit must pass against the workspace.
# ──────────────────────────────────────────────────────────────────────


def test_live_repo_passes() -> None:
    """The committed workspace must satisfy the use-cases/ guard."""
    rc = guard.main([])
    assert rc == 0, (
        "audit-no-use-cases-dir failed against the live repo. "
        "Either remove the new use-cases/ reference or, if it is "
        "legitimate historical context, add the file to ALLOWLIST_PATHS."
    )


# ──────────────────────────────────────────────────────────────────────
# Negative cases: the guard MUST trip.
# ──────────────────────────────────────────────────────────────────────


def test_directory_resurrection_is_fatal(tmp_path: Path) -> None:
    """Re-creating ``use-cases/`` must hard-fail the audit."""
    with _synthetic_repo(tmp_path):
        (tmp_path / "use-cases").mkdir()
        (tmp_path / "use-cases" / "cat-01-server-compute.md").write_text(
            "# Legacy revival attempt\n", encoding="utf-8"
        )
        _git_add_all_and_commit(tmp_path, "resurrect")

        rc = guard.main([])
        assert rc == 2


def test_new_path_reference_blocked(tmp_path: Path) -> None:
    """A new file mentioning ``use-cases/cat-`` must be flagged."""
    with _synthetic_repo(tmp_path):
        offender = tmp_path / "scripts" / "regress.py"
        offender.parent.mkdir(parents=True)
        offender.write_text(
            "# load legacy markdown\nPATH = 'use-cases/cat-01-server-compute.md'\n",
            encoding="utf-8",
        )
        _git_add_all_and_commit(tmp_path, "regress")

        rc = guard.main([])
        assert rc == 2


# ──────────────────────────────────────────────────────────────────────
# Positive cases: the guard MUST NOT trip on safe patterns.
# ──────────────────────────────────────────────────────────────────────


def test_repo_url_does_not_trip(tmp_path: Path) -> None:
    """URLs containing the repo slug ``splunk-monitoring-use-cases``
    are safe (the literal ``use-cases`` is part of the repo name,
    not a directory reference)."""
    with _synthetic_repo(tmp_path):
        f = tmp_path / "docs" / "links.md"
        f.parent.mkdir(parents=True)
        f.write_text(
            "Visit https://github.com/fenre/splunk-monitoring-use-cases/\n"
            "or https://fenre.github.io/splunk-monitoring-use-cases/.\n",
            encoding="utf-8",
        )
        _git_add_all_and_commit(tmp_path, "links")

        rc = guard.main([])
        assert rc == 0


def test_external_use_cases_url_does_not_trip(tmp_path: Path) -> None:
    """Third-party URLs that happen to contain ``/use-cases/`` are safe."""
    with _synthetic_repo(tmp_path):
        f = tmp_path / "docs" / "vendor-links.md"
        f.parent.mkdir(parents=True)
        f.write_text(
            "See https://tetragon.io/docs/use-cases/ for examples.\n",
            encoding="utf-8",
        )
        _git_add_all_and_commit(tmp_path, "vendor")

        rc = guard.main([])
        assert rc == 0


def test_allowlisted_path_is_allowed(tmp_path: Path) -> None:
    """Files on the historical-reference allowlist may keep refs."""
    with _synthetic_repo(tmp_path):
        f = tmp_path / "CHANGELOG.md"
        f.write_text(
            "## v8.2.0\n\n- Removed legacy use-cases/cat-NN-*.md monoliths.\n",
            encoding="utf-8",
        )
        _git_add_all_and_commit(tmp_path, "changelog")

        # CHANGELOG.md is the canonical immutable-history allowlist entry;
        # re-running the audit must stay clean even when it explicitly
        # mentions the legacy path.
        rc = guard.main([])
        assert rc == 0


# ──────────────────────────────────────────────────────────────────────
# UX surfaces.
# ──────────────────────────────────────────────────────────────────────


def test_check_flag_is_a_noop_alias() -> None:
    """``--check`` is accepted for parity with other freshness gates."""
    rc = guard.main(["--check"])
    assert rc == 0


def test_list_allowlist_prints_and_exits_clean(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = guard.main(["--list-allowlist"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "use-cases/ historical-reference allowlist" in out
    # The CLI dispatcher registry is the canary entry that must always
    # appear in the printed allowlist.
    assert "src/splunk_uc/_registry.py" in out


def test_allowlist_only_lists_existing_files() -> None:
    """Stale allowlist entries (files that no longer exist) are a smell.

    The audit silently skips them at runtime, so this test surfaces
    them explicitly. Entries that genuinely point at since-deleted
    historical files should be removed from ALLOWLIST_PATHS in the
    same commit that deletes the file."""
    missing = [rel for rel in sorted(guard.ALLOWLIST_PATHS) if not (REPO_ROOT / rel).exists()]
    assert not missing, (
        f"Stale entries in ALLOWLIST_PATHS — these files no longer exist on disk: {missing}"
    )


# ──────────────────────────────────────────────────────────────────────
# CLI smoke: invoking via ``python -m splunk_uc audit-no-use-cases-dir``.
# ──────────────────────────────────────────────────────────────────────


def test_cli_dispatcher_smoke() -> None:
    """The dispatcher must wire the new verb correctly."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run(
        ["python3", "-m", "splunk_uc", "audit-no-use-cases-dir"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"dispatcher smoke failed:\nstdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    )
    assert "no use-cases/ directory" in res.stdout


# Silence an unused-imports warning.
_ = io
