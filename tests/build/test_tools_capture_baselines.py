"""Unit-level coverage for ``tools/capture_baselines.py``.

``capture_baselines`` snapshots the repo's size, file-count and
build-timing footprint into ``data/baselines/v<VERSION>.json``. The
repo-overhaul plan §7 references these numbers as the floor for
every later "X% smaller" or "Y× faster" target — without a baseline
file those targets are unverifiable.

The script is invoked by the ``baseline`` Makefile target. Before
this commit it had zero unit tests
(``Module tools.capture_baselines was never imported`` warning).

What this suite locks
---------------------

* ``_file_sizes`` returns ``{"raw": None, "gzipped": None}`` for
  missing files and ``{"raw": N, "gzipped": M}`` (with M smaller
  than N for compressible payloads) for present files.
* ``_du_kb`` returns None for missing directories, ``0`` for an
  empty directory, and the total bytes / 1024 for a populated
  tree (including nested subdirectories). Files that throw OSError
  on stat() are silently skipped (the ``except OSError: pass``
  branch).
* ``_count_files`` returns the number of recursive matches.
* ``_count_uc_headings`` returns 0 when ``use-cases/`` is absent,
  counts lines starting with ``"### UC-"`` across every
  ``cat-*.md`` file when present.
* ``_validate_yml_steps`` returns None when the workflow file is
  absent and the count of lines starting with ``- name:`` when
  present.
* ``_git_head`` returns the git SHA when ``git`` succeeds and None
  on every documented failure mode (CalledProcessError, OSError,
  FileNotFoundError, SubprocessError).
* ``_maybe_run_build`` returns the documented dict on success
  (``wall_seconds``, ``exit_code``, ``stderr_tail``) and the
  error dict on ``SubprocessError``.
* ``capture`` assembles the full snapshot with the documented
  top-level keys, falls back to "unknown" version when the VERSION
  file is absent, includes a ``make_build`` block under timing
  only when ``run_build=True``.
* ``main`` writes the snapshot to the default
  ``data/baselines/v<VERSION>.json`` location when ``--output``
  is omitted, honours ``--output`` when provided (creating the
  parent dir), honours ``--build`` by including the make_build
  block, honours ``--version``, and returns 0.
* The ``if __name__ == "__main__":`` guard is exercised by an
  in-process smoke check (we don't actually run the script as a
  subprocess to avoid expensive build-pipeline side effects).

Run
---

``pytest tests/build/test_tools_capture_baselines.py``

Coverage check
--------------

``pytest tests/build/test_tools_capture_baselines.py \
    --cov=tools.capture_baselines --cov-branch``
"""
from __future__ import annotations

import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import tools.capture_baselines as capture_baselines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect ``REPO_ROOT`` to ``tmp_path``."""

    monkeypatch.setattr(capture_baselines, "REPO_ROOT", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# _file_sizes
# ---------------------------------------------------------------------------


class TestFileSizes:
    def test_missing_file_returns_none_pair(self, tmp_path: Path) -> None:
        result = capture_baselines._file_sizes(tmp_path / "absent.txt")
        assert result == {"raw": None, "gzipped": None}

    def test_present_file_returns_raw_and_gzipped(
        self, tmp_path: Path
    ) -> None:
        """A compressible payload yields gzipped < raw."""

        path = tmp_path / "big.txt"
        path.write_text("a" * 10_000, encoding="utf-8")
        result = capture_baselines._file_sizes(path)
        assert result["raw"] == 10_000
        assert isinstance(result["gzipped"], int)
        assert 0 < result["gzipped"] < 10_000

    def test_present_empty_file(self, tmp_path: Path) -> None:
        """Empty file -> raw=0, gzipped is a small constant overhead
        (the gzip header)."""

        path = tmp_path / "empty.txt"
        path.write_bytes(b"")
        result = capture_baselines._file_sizes(path)
        assert result["raw"] == 0
        assert isinstance(result["gzipped"], int)
        # Bare gzip header is ~20 bytes, but pin only that it's >= 0.
        assert result["gzipped"] >= 0


# ---------------------------------------------------------------------------
# _du_kb
# ---------------------------------------------------------------------------


class TestDuKb:
    def test_missing_dir_returns_none(self, tmp_path: Path) -> None:
        assert capture_baselines._du_kb(tmp_path / "missing") is None

    def test_empty_dir_returns_zero(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty"
        empty.mkdir()
        assert capture_baselines._du_kb(empty) == 0

    def test_walks_nested_subdirectories(self, tmp_path: Path) -> None:
        root = tmp_path / "root"
        (root / "a" / "b").mkdir(parents=True)
        (root / "x.txt").write_bytes(b"a" * 1024)
        (root / "a" / "y.txt").write_bytes(b"b" * 2048)
        (root / "a" / "b" / "z.txt").write_bytes(b"c" * 4096)
        # Total: 7168 bytes / 1024 = 7
        assert capture_baselines._du_kb(root) == 7

    def test_skips_files_that_fail_stat(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Files that raise OSError on .stat() are silently skipped
        (covers the ``except OSError: pass`` arm)."""

        root = tmp_path / "root"
        root.mkdir()
        (root / "good.txt").write_bytes(b"x" * 2048)

        original_stat = Path.stat

        def _selective_boom(self: Path) -> os.stat_result:
            if self.name == "good.txt":
                raise OSError("simulated stat failure")
            return original_stat(self)

        monkeypatch.setattr(Path, "stat", _selective_boom)
        # The single tracked file raises OSError and is skipped ->
        # total ends up at 0 KiB, not at a partial count.
        result = capture_baselines._du_kb(root)
        assert result == 0


# ---------------------------------------------------------------------------
# _count_files
# ---------------------------------------------------------------------------


class TestCountFiles:
    def test_recursive_glob_counts_all_matches(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "x.json").touch()
        (tmp_path / "a" / "y.json").touch()
        (tmp_path / "z.json").touch()
        assert capture_baselines._count_files("*.json", root=tmp_path) == 3


# ---------------------------------------------------------------------------
# _count_uc_headings
# ---------------------------------------------------------------------------


class TestCountUcHeadings:
    def test_missing_use_cases_returns_zero(
        self,
        isolated_repo: Path,
    ) -> None:
        assert capture_baselines._count_uc_headings() == 0

    def test_counts_uc_headings(
        self,
        isolated_repo: Path,
    ) -> None:
        use_cases = isolated_repo / "use-cases"
        use_cases.mkdir()
        (use_cases / "cat-01-foo.md").write_text(
            "# Cat 1\n### UC-1.1.1 Title\n### UC-1.1.2 Title\n"
            "Some other line\n### UC-1.2.1 Title\n",
            encoding="utf-8",
        )
        (use_cases / "cat-02-bar.md").write_text(
            "### UC-2.1.1 Title\n", encoding="utf-8"
        )
        assert capture_baselines._count_uc_headings() == 4

    def test_ignores_non_cat_md(
        self,
        isolated_repo: Path,
    ) -> None:
        """Only ``cat-*.md`` files are walked (the glob pattern)."""

        use_cases = isolated_repo / "use-cases"
        use_cases.mkdir()
        (use_cases / "not-cat.md").write_text(
            "### UC-1.1.1 Title\n", encoding="utf-8"
        )
        assert capture_baselines._count_uc_headings() == 0


# ---------------------------------------------------------------------------
# _validate_yml_steps
# ---------------------------------------------------------------------------


class TestValidateYmlSteps:
    def test_missing_workflow_returns_none(
        self,
        isolated_repo: Path,
    ) -> None:
        assert capture_baselines._validate_yml_steps() is None

    def test_counts_name_lines(
        self,
        isolated_repo: Path,
    ) -> None:
        workflow = isolated_repo / ".github" / "workflows" / "validate.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(
            "jobs:\n"
            "  test:\n"
            "    steps:\n"
            "      - name: Step One\n"
            "        run: echo 1\n"
            "      - name: Step Two\n"
            "        run: echo 2\n"
            "      - name: Step Three\n",
            encoding="utf-8",
        )
        assert capture_baselines._validate_yml_steps() == 3


# ---------------------------------------------------------------------------
# _git_head
# ---------------------------------------------------------------------------


class TestGitHead:
    def test_returns_sha_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "deadbeef\n"
        )
        assert capture_baselines._git_head() == "deadbeef"

    @pytest.mark.parametrize(
        "exc",
        [
            subprocess.CalledProcessError(128, ["git"]),
            FileNotFoundError("git not installed"),
            OSError("disk gone"),
            subprocess.SubprocessError("generic"),
        ],
    )
    def test_returns_none_on_documented_errors(
        self,
        exc: Exception,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _boom(*_a, **_k):
            raise exc

        monkeypatch.setattr(subprocess, "check_output", _boom)
        assert capture_baselines._git_head() is None


# ---------------------------------------------------------------------------
# _maybe_run_build
# ---------------------------------------------------------------------------


class TestMaybeRunBuild:
    def test_success_returns_wall_seconds_and_exit_code(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successful run -> wall_seconds is a float, exit_code
        matches, stderr_tail is a list (last 3 lines)."""

        class _FakeCompleted:
            returncode = 0
            stderr = "line1\nline2\nline3\nline4\n"

        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _FakeCompleted()
        )
        result = capture_baselines._maybe_run_build()
        assert isinstance(result["wall_seconds"], float)
        assert result["exit_code"] == 0
        # Last 3 lines of the fake stderr.
        assert result["stderr_tail"] == ["line2", "line3", "line4"]

    def test_empty_stderr_returns_empty_tail(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty stderr -> stderr_tail is ``[]`` (covers the False
        arm of the ``if result.stderr`` ternary)."""

        class _FakeCompleted:
            returncode = 0
            stderr = ""

        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _FakeCompleted()
        )
        result = capture_baselines._maybe_run_build()
        assert result["stderr_tail"] == []

    def test_subprocess_error_returns_error_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any ``SubprocessError`` (incl. TimeoutExpired) -> documented
        error dict with wall_seconds/exit_code both None."""

        def _boom(*_a, **_k):
            raise subprocess.TimeoutExpired(cmd=["x"], timeout=1)

        monkeypatch.setattr(subprocess, "run", _boom)
        result = capture_baselines._maybe_run_build()
        assert result["wall_seconds"] is None
        assert result["exit_code"] is None
        assert "error" in result


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------


class TestCapture:
    def test_version_falls_back_to_unknown_when_file_absent(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """No VERSION file -> 'unknown' literal goes into the
        snapshot."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(run_build=False, version=None)
        assert snap["version"] == "unknown"

    def test_version_read_from_file(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (isolated_repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(run_build=False, version=None)
        assert snap["version"] == "9.9.9"

    def test_explicit_version_overrides_file(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (isolated_repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(
            run_build=False, version="custom-label"
        )
        assert snap["version"] == "custom-label"

    def test_snapshot_includes_documented_top_level_keys(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The snapshot dict carries the documented shape — pin this
        so downstream consumers don't get silently broken."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(
            run_build=False, version="v1"
        )
        for key in (
            "$schema",
            "version",
            "captured_at",
            "git_head",
            "tracked_file_sizes_bytes",
            "counts",
            "tree_sizes_kb",
            "timing",
            "notes",
        ):
            assert key in snap

    def test_counts_include_uc_md_companions_zero_legacy(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The legacy ``uc_md_companions`` field is pinned at 0 for
        backward-compat with the v7 baseline schema (deprecated
        2026-05-18)."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(run_build=False, version="v1")
        assert snap["counts"]["uc_md_companions"] == 0

    def test_run_build_true_adds_make_build_block(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``run_build=True`` injects the ``make_build`` block under
        timing (we monkey-patch ``_maybe_run_build`` to avoid the
        real build pipeline)."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        monkeypatch.setattr(
            capture_baselines,
            "_maybe_run_build",
            lambda: {"wall_seconds": 12.34, "exit_code": 0},
        )
        snap = capture_baselines.capture(
            run_build=True, version="v1"
        )
        timing = snap["timing"]
        assert isinstance(timing, dict)
        assert "make_build" in timing
        assert timing["make_build"]["wall_seconds"] == 12.34

    def test_run_build_false_omits_make_build_block(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``run_build=False`` (default) leaves the ``timing`` block
        with the original placeholders only."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(
            run_build=False, version="v1"
        )
        timing = snap["timing"]
        assert isinstance(timing, dict)
        assert "make_build" not in timing
        assert timing["make_build_wall_seconds"] is None

    def test_counts_optional_directories_present(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When ``scripts/``, ``samples/`` and ``content/`` exist
        the counters reflect their contents (covers the True arm
        of each ``... .exists()`` ternary in the counts block)."""

        (isolated_repo / "scripts").mkdir()
        (isolated_repo / "scripts" / "a.py").touch()
        (isolated_repo / "scripts" / "b.py").touch()
        (isolated_repo / "samples").mkdir()
        (isolated_repo / "samples" / "x").mkdir()
        (isolated_repo / "samples" / "y").mkdir()
        (isolated_repo / "samples" / "z.txt").touch()  # not a dir
        cat_dir = isolated_repo / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        (cat_dir / "_category.json").touch()
        (cat_dir / "UC-1.1.1.json").touch()

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        snap = capture_baselines.capture(run_build=False, version="v1")
        counts = snap["counts"]
        assert counts["scripts_total"] == 2
        # Only directories under samples/ are counted.
        assert counts["samples_dirs"] == 2
        assert counts["categories"] == 1
        assert counts["uc_json_sidecars"] == 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_default_output_path(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without ``--output``, writes to
        ``data/baselines/v<VERSION>.json``."""

        (isolated_repo / "VERSION").write_text("9.9.9", encoding="utf-8")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        rc = capture_baselines.main([])
        assert rc == 0
        expected = isolated_repo / "data" / "baselines" / "v9.9.9.json"
        assert expected.exists()
        snap = json.loads(expected.read_text(encoding="utf-8"))
        assert snap["version"] == "9.9.9"
        out = capsys.readouterr().out
        assert "Wrote baseline to" in out

    def test_explicit_output_path(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """``--output`` honours an explicit destination and creates
        intermediate directories. The output path MUST be inside
        the isolated repo because main prints
        ``output.relative_to(REPO_ROOT)`` which raises ValueError
        if the path is outside REPO_ROOT."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        out_path = isolated_repo / "x" / "y" / "snap.json"
        rc = capture_baselines.main(["--output", str(out_path)])
        assert rc == 0
        assert out_path.exists()

    def test_version_override_used(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``--version`` overrides both the VERSION file and the
        documented default. Output path uses the overridden value."""

        (isolated_repo / "VERSION").write_text("1.0.0", encoding="utf-8")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        rc = capture_baselines.main(["--version", "abc"])
        assert rc == 0
        assert (isolated_repo / "data" / "baselines" / "vabc.json").exists()

    def test_build_flag_includes_make_build(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``--build`` triggers ``_maybe_run_build`` and embeds the
        result under timing.make_build."""

        (isolated_repo / "VERSION").write_text("1.0.0", encoding="utf-8")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: "sha\n"
        )
        monkeypatch.setattr(
            capture_baselines,
            "_maybe_run_build",
            lambda: {"wall_seconds": 0.5, "exit_code": 0},
        )
        rc = capture_baselines.main(["--build"])
        assert rc == 0
        snap = json.loads(
            (isolated_repo / "data" / "baselines" / "v1.0.0.json").read_text(
                encoding="utf-8"
            )
        )
        assert snap["timing"]["make_build"]["wall_seconds"] == 0.5


# ---------------------------------------------------------------------------
# Module entrypoint guard
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_writes_baseline(
        self,
        tmp_path: Path,
    ) -> None:
        """Smoke test: invoke the script as ``python -m
        tools.capture_baselines`` against the real repo with
        ``--output`` pointed at tmp_path. This exercises the
        ``if __name__`` guard. The default build is NOT run (no
        ``--build``) so the test stays fast."""

        repo_root = Path(capture_baselines.__file__).resolve().parent.parent
        if not (repo_root / "VERSION").exists():
            pytest.skip("repo has no VERSION file")
        # ``main`` writes the snapshot relative to REPO_ROOT, so
        # we need the output path to be INSIDE the repo root to
        # avoid the ``relative_to`` ValueError. Use a tmp file
        # under the repo's tests/ tree (cleaned up after).
        out_path = repo_root / "tests" / "_baseline_smoke.json"
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.capture_baselines",
                    "--output",
                    str(out_path),
                ],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, (
                f"rc={result.returncode} "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
            assert out_path.exists()
            snap = json.loads(out_path.read_text(encoding="utf-8"))
            assert "version" in snap
            assert "captured_at" in snap
        finally:
            if out_path.exists():
                out_path.unlink()
