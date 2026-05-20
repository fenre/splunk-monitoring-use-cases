"""Hermetic unit tests for ``splunk_uc.audits.build_reproducibility``.

P16 wave TT (2026-05-19). The audit invokes ``tools/build/build.py`` twice
to assert that two ``--reproducible`` builds produce byte-identical
``integrity.json`` files. The tests stub out every subprocess and
filesystem touch so the full coverage matrix runs in <50ms with no
network, no git, and no real build.

Tests pin every documented contract:

* Module-level constants (``PROJECT_ROOT`` walks three parents up per
  ADR-0009, ``BUILD_SCRIPT`` is ``tools/build/build.py``).
* The ``_git_commit_epoch`` / ``_git_head_sha`` matrix (success returns
  stripped string; ``CalledProcessError`` and ``FileNotFoundError``
  both raise ``RuntimeError`` wrapping the cause).
* The ``_run_build`` matrix (forwards stdout/stderr by inheritance,
  pins ``SOURCE_DATE_EPOCH`` via env, returns the subprocess exit code).
* The ``_read_integrity`` matrix (present file returns raw bytes,
  missing file raises ``FileNotFoundError`` with the absolute path).
* The full ``main()`` exit-code matrix:
  - rc_a != 0 -> exit 2 with ``FAIL: first build exited`` stderr,
  - first build runs but integrity.json missing -> exit 2,
  - ``--first-build-only`` short-circuits after first build -> exit 0,
  - rc_b != 0 -> exit 2 with ``FAIL: second build exited`` stderr,
  - second build runs but integrity.json missing -> exit 2,
  - HEAD sha drifts mid-run -> exit 2,
  - integrity bytes differ -> exit 1 with cleanup_paths cleared,
  - PASS -> exit 0 with byte count rendered in success line,
  - ``--keep`` keeps temp dir + prints path to stderr,
  - cleanup ``shutil.rmtree`` suppresses ``OSError``,
  - ``argv=None`` falls through to ``sys.argv`` default.
"""

from __future__ import annotations

import pathlib
import subprocess
from typing import Any

import pytest

import splunk_uc.audits.build_reproducibility as br


# ----------------------------------------------------------------- module-level
def test_project_root_walks_three_parents_up() -> None:
    """``PROJECT_ROOT`` is build_reproducibility -> audits -> splunk_uc -> src -> repo."""
    here = pathlib.Path(br.__file__).resolve()
    assert br.PROJECT_ROOT == here.parents[3]
    assert (br.PROJECT_ROOT / "tools" / "build" / "build.py").exists()


def test_build_script_constant_targets_tools_build_buildpy() -> None:
    assert br.BUILD_SCRIPT == br.PROJECT_ROOT / "tools" / "build" / "build.py"


# --------------------------------------------------------------- git helpers ---
def test_git_commit_epoch_returns_stripped_decoded_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Success path returns the stripped UTF-8 decoded git output."""

    def fake_check_output(cmd: list[str], **_kw: Any) -> bytes:
        assert cmd == ["git", "log", "-1", "--format=%ct", "HEAD"]
        return b"1715000000\n"

    monkeypatch.setattr(br.subprocess, "check_output", fake_check_output)
    assert br._git_commit_epoch() == "1715000000"


def test_git_commit_epoch_called_process_error_raises_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``CalledProcessError`` from git is wrapped in ``RuntimeError``."""

    def boom(*_a: Any, **_kw: Any) -> bytes:
        raise subprocess.CalledProcessError(returncode=128, cmd=["git"])

    monkeypatch.setattr(br.subprocess, "check_output", boom)
    with pytest.raises(RuntimeError, match="unable to read git HEAD epoch"):
        br._git_commit_epoch()


def test_git_commit_epoch_missing_git_raises_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``FileNotFoundError`` (no git binary on PATH) is wrapped in ``RuntimeError``."""

    def boom(*_a: Any, **_kw: Any) -> bytes:
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(br.subprocess, "check_output", boom)
    with pytest.raises(RuntimeError, match="unable to read git HEAD epoch"):
        br._git_commit_epoch()


def test_git_head_sha_returns_stripped_decoded_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_check_output(cmd: list[str], **_kw: Any) -> bytes:
        assert cmd == ["git", "rev-parse", "HEAD"]
        return b"deadbeef" * 5 + b"\n"

    monkeypatch.setattr(br.subprocess, "check_output", fake_check_output)
    assert br._git_head_sha() == "deadbeef" * 5


def test_git_head_sha_called_process_error_raises_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_a: Any, **_kw: Any) -> bytes:
        raise subprocess.CalledProcessError(returncode=128, cmd=["git"])

    monkeypatch.setattr(br.subprocess, "check_output", boom)
    with pytest.raises(RuntimeError, match="unable to read git HEAD sha"):
        br._git_head_sha()


def test_git_head_sha_missing_git_raises_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_a: Any, **_kw: Any) -> bytes:
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(br.subprocess, "check_output", boom)
    with pytest.raises(RuntimeError, match="unable to read git HEAD sha"):
        br._git_head_sha()


# ----------------------------------------------------------- _run_build ---
def test_run_build_forwards_args_and_env_and_returns_rc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """``_run_build`` calls subprocess.call with the right args/env/cwd
    and forwards the exit code unchanged.
    """
    captured: dict[str, Any] = {}

    def fake_call(cmd: list[str], **kw: Any) -> int:
        captured["cmd"] = cmd
        captured["cwd"] = kw["cwd"]
        captured["env"] = kw["env"]
        return 42

    monkeypatch.setattr(br.subprocess, "call", fake_call)
    rc = br._run_build(tmp_path / "out", epoch="1700000000")
    assert rc == 42
    assert captured["cmd"][0] == br.sys.executable
    assert captured["cmd"][1] == str(br.BUILD_SCRIPT)
    assert captured["cmd"][2] == "--out"
    assert captured["cmd"][3] == str(tmp_path / "out")
    assert captured["cmd"][4] == "--reproducible"
    assert captured["cwd"] == str(br.PROJECT_ROOT)
    assert captured["env"]["SOURCE_DATE_EPOCH"] == "1700000000"


def test_run_build_overrides_existing_source_date_epoch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Caller's pre-existing ``SOURCE_DATE_EPOCH`` is overwritten."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "999")
    captured: dict[str, str] = {}

    def fake_call(_cmd: list[str], **kw: Any) -> int:
        captured["epoch"] = kw["env"]["SOURCE_DATE_EPOCH"]
        return 0

    monkeypatch.setattr(br.subprocess, "call", fake_call)
    br._run_build(tmp_path / "out", epoch="1700000000")
    assert captured["epoch"] == "1700000000"


# ----------------------------------------------------------- _read_integrity ---
def test_read_integrity_returns_bytes_when_present(
    tmp_path: pathlib.Path,
) -> None:
    out = tmp_path / "build"
    out.mkdir()
    (out / "integrity.json").write_bytes(b'{"hello":"world"}')
    assert br._read_integrity(out) == b'{"hello":"world"}'


def test_read_integrity_raises_when_missing(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "build"
    out.mkdir()
    with pytest.raises(FileNotFoundError, match="missing"):
        br._read_integrity(out)


def test_read_integrity_raises_when_path_is_dir(tmp_path: pathlib.Path) -> None:
    """If ``integrity.json`` is itself a directory, ``is_file()`` is False."""
    out = tmp_path / "build"
    (out / "integrity.json").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="missing"):
        br._read_integrity(out)


# ---------------------------------------------------------- main() — helpers ---
def _patch_git_helpers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    epoch: str = "1700000000",
    before: str = "a" * 40,
    after: str | None = None,
) -> None:
    """Stub the two git helpers; ``after`` defaults to ``before`` (no drift)."""
    monkeypatch.setattr(br, "_git_commit_epoch", lambda: epoch)
    head_seq = [before, after if after is not None else before]

    def fake_head() -> str:
        return head_seq.pop(0)

    monkeypatch.setattr(br, "_git_head_sha", fake_head)


def _patch_tempfile_mkdtemp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> pathlib.Path:
    """Force ``tempfile.mkdtemp`` to return a controlled directory."""
    root = tmp_path / "build-repro-stub"
    root.mkdir()

    def fake_mkdtemp(*_a: Any, **_kw: Any) -> str:
        return str(root)

    monkeypatch.setattr(br.tempfile, "mkdtemp", fake_mkdtemp)
    return root


# ------------------------------------------------------------- main() — happy ---
def test_main_pass_two_identical_builds(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The happy path: two builds, identical integrity, exit 0."""
    _patch_git_helpers(monkeypatch)
    root = _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, *, epoch: str) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b'{"v": "1.0"}')
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 0
    out = capsys.readouterr().out
    assert "audit_build_reproducibility: HEAD=" in out
    assert "first build OK" in out
    assert "PASS - two builds byte-identical" in out
    assert "12 bytes integrity each" in out
    assert not root.exists()  # cleanup deleted the temp dir


def test_main_pass_renders_head_short_and_full_epoch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Header line prints HEAD[:12] + the full epoch."""
    _patch_git_helpers(monkeypatch, epoch="1715009876", before="b" * 40)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"x")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    br.main([])
    out = capsys.readouterr().out
    assert "HEAD=bbbbbbbbbbbb" in out
    assert "epoch=1715009876" in out


def test_main_argv_none_falls_through_to_sys_argv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """``main(argv=None)`` reads ``sys.argv`` via argparse default."""
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"y")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    monkeypatch.setattr(br.sys, "argv", ["audit"])
    assert br.main() == 0


def test_main_help_prints_help_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--help`` exits 0 via argparse and prints the three flags."""
    with pytest.raises(SystemExit) as exc:
        br.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--check" in out
    assert "--keep" in out
    assert "--first-build-only" in out


# ----------------------------------------------------------- main() — first build
def test_main_first_build_nonzero_exit_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)
    monkeypatch.setattr(br, "_run_build", lambda *_a, **_kw: 7)
    assert br.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: first build exited 7" in err


def test_main_first_build_missing_integrity_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """First build succeeds but doesn't emit ``integrity.json``."""
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: first build did not emit integrity.json" in err


def test_main_first_build_only_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--first-build-only`` returns 0 after one successful build."""
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    call_count = {"n": 0}

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        call_count["n"] += 1
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"first-only")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main(["--first-build-only"]) == 0
    out = capsys.readouterr().out
    assert "--first-build-only => skipping second build" in out
    assert call_count["n"] == 1


# --------------------------------------------------------- main() — second build
def test_main_second_build_nonzero_exit_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    seq = iter([0, 9])

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        rc = next(seq)
        if rc == 0:
            (out_dir / "integrity.json").write_bytes(b"first-ok")
        return rc

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: second build exited 9" in err


def test_main_second_build_missing_integrity_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    call_idx = {"n": 0}

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        call_idx["n"] += 1
        out_dir.mkdir(parents=True, exist_ok=True)
        if call_idx["n"] == 1:
            (out_dir / "integrity.json").write_bytes(b"first-ok")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: second build did not emit integrity.json" in err


# -------------------------------------------------- main() — mid-audit HEAD drift
def test_main_head_drift_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Two identical builds but HEAD moved mid-audit -> exit 2."""
    _patch_git_helpers(
        monkeypatch,
        before="a" * 40,
        after="b" * 40,
    )
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"same")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: HEAD moved during audit" in err
    assert "aaaaaaaaaaaa -> bbbbbbbbbbbb" in err


# --------------------------------------------- main() — integrity mismatch -> 1
def test_main_integrity_mismatch_returns_one_and_keeps_temp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Mismatch returns 1 AND clears ``cleanup_paths`` to keep diff visible."""
    _patch_git_helpers(monkeypatch)
    root = _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    seq = iter([b"first-bytes", b"second-bytes"])

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(next(seq))
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main([]) == 1
    err = capsys.readouterr().err
    assert "FAIL: integrity.json differs" in err
    assert "build-a:" in err
    assert "build-b:" in err
    assert root.exists()  # cleanup was skipped so the diff is visible


# --------------------------------------------------------- main() — --keep mode
def test_main_keep_preserves_temp_dir_and_prints_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _patch_git_helpers(monkeypatch)
    root = _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"keep")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)
    assert br.main(["--keep"]) == 0
    err = capsys.readouterr().err
    assert f"Keeping temp builds at: {root}" in err
    assert root.exists()


def test_main_keep_also_preserves_temp_dir_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--keep keeps the temp dir even when the audit fails."""
    _patch_git_helpers(monkeypatch)
    root = _patch_tempfile_mkdtemp(monkeypatch, tmp_path)
    monkeypatch.setattr(br, "_run_build", lambda *_a, **_kw: 3)
    assert br.main(["--keep"]) == 2
    err = capsys.readouterr().err
    assert "FAIL: first build exited 3" in err
    assert f"Keeping temp builds at: {root}" in err
    assert root.exists()


# --------------------------------------------------- main() — cleanup OSError
def test_main_cleanup_suppresses_oserror(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    """``shutil.rmtree`` raising ``OSError`` is swallowed by the cleanup loop."""
    _patch_git_helpers(monkeypatch)
    _patch_tempfile_mkdtemp(monkeypatch, tmp_path)

    def fake_run_build(out_dir: pathlib.Path, **_kw: Any) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "integrity.json").write_bytes(b"matching")
        return 0

    monkeypatch.setattr(br, "_run_build", fake_run_build)

    def boom_rmtree(*_a: Any, **_kw: Any) -> None:
        raise OSError("simulated rmtree failure")

    monkeypatch.setattr(br.shutil, "rmtree", boom_rmtree)
    # No exception propagates and the audit still returns 0.
    assert br.main([]) == 0


# ------------------------------------------ smoke: `python -m ...` entry point
def test_module_dunder_main_exists() -> None:
    """Module declares ``__main__`` block — pinned for the dispatcher."""
    src = pathlib.Path(br.__file__).read_text()
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
