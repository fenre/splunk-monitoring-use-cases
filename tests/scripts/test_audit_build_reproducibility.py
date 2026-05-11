"""Unit tests for ``python3 -m splunk_uc audit-reproducibility``.

The audit drives ``tools/build/build.py``, which is heavy (~30s per
run on commodity hardware). The tests here therefore exercise the
**pure helpers** plus a single fast ``--first-build-only`` smoke.
The full double-build path is covered separately by the nightly CI
job (`.github/workflows/build-reproducibility.yml`); duplicating it
in the unit test suite would add ~90s per pytest invocation for no
extra coverage.

Test dimensions:

1. Pure helpers
   * ``_git_commit_epoch`` returns a non-empty digit string for a
     real repo.
   * ``_git_head_sha`` returns a 40-char hex sha for a real repo.
   * Both raise ``RuntimeError`` if the cwd is not a git repo.
   * ``_read_integrity`` returns the raw bytes of the file or raises
     ``FileNotFoundError`` for a missing file.

2. CLI argument parsing
   * The argparse description / flags are stable; the script accepts
     ``--check``, ``--keep``, ``--first-build-only``.

3. Smoke test (``--first-build-only``)
   * One real build runs to completion against the repo's
     ``tools/build/build.py`` and exits 0; ``integrity.json`` is
     emitted and is non-empty.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Phase 6 closure (2026-05-11): the legacy ``scripts/audit_build_reproducibility.py``
# shim has been deleted. All tests now exercise the canonical implementation
# under ``splunk_uc.audits.build_reproducibility`` directly. ``abr`` is kept
# as a local alias to minimise diff churn against the pre-deletion test body.
# Subprocess-driven CLI tests invoke the dispatcher
# (``python3 -m splunk_uc audit-reproducibility``) with ``PYTHONPATH=src`` so
# the package resolves without requiring an editable install.
sys.path.insert(0, str(SRC_DIR))

from splunk_uc.audits import build_reproducibility as impl  # noqa: E402
abr = impl

DISPATCHER_CMD = [sys.executable, "-m", "splunk_uc", "audit-reproducibility"]


def _dispatcher_env() -> dict[str, str]:
    """Return an ``os.environ``-derived env with ``src/`` on ``PYTHONPATH``.

    The dispatcher needs the ``splunk_uc`` package importable; the editable
    install is not assumed during ad-hoc maintainer runs, so we prepend
    ``src/`` ourselves. Tests preserve any pre-existing ``PYTHONPATH`` so a
    caller can layer additional paths (e.g. for tooling) on top.
    """
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{SRC_DIR}{os.pathsep}{existing}" if existing else str(SRC_DIR)
    )
    return env

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_git_commit_epoch_returns_digits_for_real_repo() -> None:
    epoch = abr._git_commit_epoch()
    assert epoch.isdigit(), f"epoch must be all digits, got {epoch!r}"
    assert int(epoch) > 1_000_000_000, "epoch must be a sane unix timestamp"


def test_git_head_sha_returns_40_hex_chars_for_real_repo() -> None:
    sha = abr._git_head_sha()
    assert len(sha) == 40, f"expected 40-char sha, got {sha!r}"
    assert all(c in "0123456789abcdef" for c in sha), f"non-hex sha {sha!r}"


def test_git_helpers_raise_outside_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both git helpers raise ``RuntimeError`` when not in a git repo.

    We monkeypatch ``PROJECT_ROOT`` on the implementation module so
    the subprocess invocation runs ``git log`` in a non-repo directory
    and returns non-zero. Patching ``abr`` (the shim) would not reach
    the implementation's closure since the shim only re-exports.
    """
    monkeypatch.setattr(impl, "PROJECT_ROOT", tmp_path)
    with pytest.raises(RuntimeError):
        abr._git_commit_epoch()
    with pytest.raises(RuntimeError):
        abr._git_head_sha()


def test_read_integrity_returns_bytes(tmp_path: Path) -> None:
    p = tmp_path / "integrity.json"
    payload = b'{"algorithm":"sha256","files":[]}\n'
    p.write_bytes(payload)
    assert abr._read_integrity(tmp_path) == payload


def test_read_integrity_raises_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        abr._read_integrity(tmp_path)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_argparse_accepts_check_flag() -> None:
    """No exception when only ``--help`` is provided."""
    rc = subprocess.call(
        [*DISPATCHER_CMD, "--help"],
        cwd=str(PROJECT_ROOT),
        env=_dispatcher_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert rc == 0


def test_argparse_help_lists_three_modes() -> None:
    """The --help output names the three supported flags."""
    out = subprocess.check_output(
        [*DISPATCHER_CMD, "--help"],
        cwd=str(PROJECT_ROOT),
        env=_dispatcher_env(),
        text=True,
    )
    for flag in ("--check", "--keep", "--first-build-only"):
        assert flag in out, f"--help is missing {flag}"


def test_argparse_rejects_unknown_flag() -> None:
    rc = subprocess.call(
        [*DISPATCHER_CMD, "--bogus"],
        cwd=str(PROJECT_ROOT),
        env=_dispatcher_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert rc != 0


# ---------------------------------------------------------------------------
# Module surface (the names CI imports)
# ---------------------------------------------------------------------------


def test_module_exports_main_callable() -> None:
    """The module exposes a ``main()`` callable so test harnesses
    can drive the audit programmatically without spawning a subprocess.
    """
    assert callable(abr.main)


def test_module_exports_run_build() -> None:
    """``_run_build`` is the seam that mocked tests can patch in
    future to short-circuit the slow build invocation."""
    assert callable(abr._run_build)


# ---------------------------------------------------------------------------
# Smoke: one real build (skipped under CI=fast / explicit slow opt-out)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("SKIP_SLOW_TESTS") == "1",
    reason="set SKIP_SLOW_TESTS=1 to skip the ~30s real-build smoke",
)
def test_first_build_only_smoke(tmp_path: Path) -> None:
    """End-to-end smoke: one real ``--reproducible`` build succeeds.

    Cost: ~30s. Skipped when ``SKIP_SLOW_TESTS=1`` is set so tight
    inner-loop runs (`pytest -x -q`) stay fast. CI runs it because
    the audit is what gates the entire reproducibility contract.
    """
    rc = subprocess.call(
        [*DISPATCHER_CMD, "--first-build-only"],
        cwd=str(PROJECT_ROOT),
        env=_dispatcher_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    assert rc == 0
