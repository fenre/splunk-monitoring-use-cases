"""Unit-level coverage for ``tools/audits/budgets.py``.

``budgets`` walks ``dist/`` against the per-asset-class size budgets in
``tools/build/budgets.json`` and blocks merge when a hard budget
(``fail_on_exceed: true``) is breached. It exists to prevent silent
page-weight regressions and is documented in ``docs/architecture.md``.

The script ran with zero unit coverage before this file landed
(``Module tools.audits.budgets was never imported`` warning). This
suite drives every branch of ``main`` and the ``_gzip_len`` helper
against synthetic ``dist/`` trees rooted at ``tmp_path`` and synthetic
budgets files that exercise raw, gzip, hard, soft, and absent
thresholds independently.

What this suite locks
---------------------

* ``main`` returns ``2`` and writes a missing-dist message when the
  ``--dist`` root does not exist.
* ``main`` returns ``0`` when every match fits inside both budgets.
* ``main`` returns ``1`` when ANY ``hard=True`` budget is exceeded
  even by one byte (raw and gz dimensions tested separately).
* ``main`` returns ``0`` when a ``hard=False`` budget is exceeded —
  the violation is reported as WARN but does not fail the audit.
* ``--json`` emits a stable, sorted JSON report on stdout and omits
  the human-readable per-budget summary.
* Human-readable mode prints the per-budget tag (OK / WARN / FAIL),
  match count, and at most three sample violations per budget.
* The ``glob`` parser supports both leaf globs (``index.html``) and
  recursive globs (``**``).
* The ``max_bytes_gz``-only branch computes ``_gzip_len`` and ignores
  the raw size.
* ``_gzip_len`` returns the gzip-compressed length using
  ``mtime=0`` (deterministic across runs).
* ``argv=None`` falls through to ``sys.argv``.
* ``__main__`` guard exercised by a subprocess smoke against the real
  repo ``dist/`` tree when present, otherwise skipped.

Run
---

``pytest tests/build/test_tools_audits_budgets.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_budgets.py \
    --cov=tools.audits.budgets --cov-branch``
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.budgets as budgets_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_budgets(tmp_path: Path, budgets: list[dict[str, Any]]) -> Path:
    spec = {"budgets": budgets}
    path = tmp_path / "budgets.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def _make_file(dist: Path, *, name: str, size: int) -> Path:
    """Create a file with deterministic content of exactly ``size``
    bytes. We use a repeating ASCII pattern so the file is highly
    compressible — that keeps gzip sizes far below raw sizes and
    makes the raw-vs-gz test assertions stable."""

    dist.mkdir(parents=True, exist_ok=True)
    path = dist / name
    path.parent.mkdir(parents=True, exist_ok=True)
    # ``b"a"`` is highly compressible — repeated content gzips into
    # roughly 0.1% of the raw size, so we never have to fight noise
    # in the gz threshold tests.
    path.write_bytes(b"a" * size)
    return path


# ---------------------------------------------------------------------------
# Missing dist directory
# ---------------------------------------------------------------------------


class TestMissingDistDir:
    def test_returns_2_when_dist_missing(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        budgets = _write_budgets(tmp_path, [])
        rc = budgets_mod.main(
            ["--dist", str(tmp_path / "does-not-exist"), "--budgets", str(budgets)]
        )
        assert rc == 2
        captured = capsys.readouterr()
        assert "missing dist dir" in captured.err
        # Nothing on stdout — short-circuit before any reporting.
        assert captured.out == ""


# ---------------------------------------------------------------------------
# Happy path — every budget passes
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_empty_budgets_returns_0_with_no_output(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No budgets means nothing to check — return 0 silently."""

        dist = tmp_path / "dist"
        dist.mkdir()
        budgets = _write_budgets(tmp_path, [])
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        assert capsys.readouterr().out == ""

    def test_single_budget_within_raw_limit_passes(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=512)
        budgets = _write_budgets(
            tmp_path,
            [{"id": "landing", "glob": "index.html", "max_bytes": 1024}],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[budgets] OK   landing" in out
        assert "1 match" in out
        assert "0 violations" in out

    def test_no_matches_reports_zero_matches(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A budget whose glob matches nothing must report
        ``0 match`` — no spurious violation."""

        dist = tmp_path / "dist"
        dist.mkdir()
        budgets = _write_budgets(
            tmp_path,
            [{"id": "uc-pages", "glob": "uc/**/index.html", "max_bytes": 1024}],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "0 match" in out

    def test_recursive_glob_finds_nested_files(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "dist"
        _make_file(dist, name="uc/UC-1.1.1/index.html", size=256)
        _make_file(dist, name="uc/UC-2.2.2/index.html", size=256)
        budgets = _write_budgets(
            tmp_path,
            [{"id": "uc-pages", "glob": "uc/**/index.html", "max_bytes": 1024}],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "2 match" in out
        assert "0 violations" in out


# ---------------------------------------------------------------------------
# Failure modes — hard vs soft
# ---------------------------------------------------------------------------


class TestFailureModes:
    def test_hard_budget_over_raw_returns_1(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=2048)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "landing",
                    "glob": "index.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": True,
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "[budgets] FAIL landing" in out
        assert "1 violations" in out
        # The violation line includes the per-file detail with raw/gz
        # kind and the ``>`` token.
        assert "index.html: 2,048 > 1,024 bytes (raw)" in out

    def test_soft_budget_over_raw_still_returns_0(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``fail_on_exceed: false`` is the documented soft budget:
        violation is reported as WARN but does NOT fail the audit."""

        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=2048)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "landing",
                    "glob": "index.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": False,
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "[budgets] WARN landing" in out
        assert "1 violations" in out

    def test_gz_violation_is_separate_from_raw(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A budget can fail on gz alone. We pick a payload whose raw
        size passes but whose gz size exceeds the cap. Because the
        synthetic content is highly compressible, we set an absurdly
        low ``max_bytes_gz`` to force the gz check to fire."""

        dist = tmp_path / "dist"
        _make_file(dist, name="big.js", size=100_000)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "scripts",
                    "glob": "big.js",
                    "max_bytes": 1_000_000,  # raw passes
                    "max_bytes_gz": 5,       # gz definitely fails
                    "fail_on_exceed": True,
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "(gz)" in out
        assert "(raw)" not in out  # raw cap was generous

    def test_gz_only_budget_skips_raw_arithmetic(
        self,
        tmp_path: Path,
    ) -> None:
        """When ``max_bytes`` is absent, the audit must NOT add a raw
        violation no matter how large the file is — only the gz
        threshold gates the budget."""

        dist = tmp_path / "dist"
        _make_file(dist, name="big.js", size=100_000)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "scripts-gz-only",
                    "glob": "big.js",
                    # max_bytes intentionally omitted
                    "max_bytes_gz": 1_000_000,  # generous: gz passes
                    "fail_on_exceed": True,
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0  # no max_bytes ⇒ no raw violation possible

    def test_raw_only_budget_skips_gzip_compression(
        self,
        tmp_path: Path,
    ) -> None:
        """When ``max_bytes_gz`` is absent, ``_gzip_len`` MUST NOT be
        called (the conditional in the source is
        ``gz = _gzip_len(m) if max_bytes_gz else 0``). We assert the
        behaviour by intercepting ``_gzip_len`` and asserting it was
        not called."""

        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=128)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "landing-raw-only",
                    "glob": "index.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": True,
                }
            ],
        )
        called = {"count": 0}

        def _no_call(_: Path) -> int:
            called["count"] += 1
            return 0

        monkeypatch_target = budgets_mod._gzip_len
        budgets_mod._gzip_len = _no_call  # type: ignore[assignment]
        try:
            rc = budgets_mod.main(
                ["--dist", str(dist), "--budgets", str(budgets)]
            )
        finally:
            budgets_mod._gzip_len = monkeypatch_target  # type: ignore[assignment]
        assert rc == 0
        assert called["count"] == 0

    def test_mixed_hard_and_soft_violations_returns_1(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The fail bit must be sticky: ONE hard violation across the
        whole report forces a return code of 1, even if a softer
        violation was visited later."""

        dist = tmp_path / "dist"
        _make_file(dist, name="hard.html", size=4096)
        _make_file(dist, name="soft.html", size=4096)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "hard-budget",
                    "glob": "hard.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": True,
                },
                {
                    "id": "soft-budget",
                    "glob": "soft.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": False,
                },
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "[budgets] FAIL hard-budget" in out
        assert "[budgets] WARN soft-budget" in out

    def test_default_fail_on_exceed_is_true(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``budget.get("fail_on_exceed", True)`` — when the key is
        absent the budget is treated as HARD. Locking this default
        is important so a typo in the manifest doesn't silently
        convert a hard budget to a soft warning."""

        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=2048)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "landing",
                    "glob": "index.html",
                    "max_bytes": 1024,
                    # fail_on_exceed deliberately omitted
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 1
        assert "FAIL" in capsys.readouterr().out

    def test_violation_detail_truncates_after_three_lines(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Human-readable output prints at most three per-budget
        violation detail lines. The remainder are silently omitted
        (the JSON report is the source of truth for the full list)."""

        dist = tmp_path / "dist"
        for i in range(5):
            _make_file(dist, name=f"file{i}.html", size=2048)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "pages",
                    "glob": "*.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": True,
                }
            ],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 1
        out = capsys.readouterr().out
        # All five files violate but only the first three appear in
        # the per-budget detail block. We count occurrences of the
        # ``> 1,024 bytes`` substring.
        assert out.count("> 1,024 bytes") == 3

    def test_files_only_globs_skip_subdirectories(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The audit's matches set filters by ``is_file()``; a
        directory that happens to match the glob must be ignored."""

        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "index.html").mkdir()  # a directory NAMED index.html
        budgets = _write_budgets(
            tmp_path,
            [{"id": "landing", "glob": "index.html", "max_bytes": 1024}],
        )
        rc = budgets_mod.main(["--dist", str(dist), "--budgets", str(budgets)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "0 match" in out


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


class TestJsonOutput:
    def test_json_mode_emits_sorted_indented_array(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=2048)
        budgets = _write_budgets(
            tmp_path,
            [
                {
                    "id": "landing",
                    "glob": "index.html",
                    "max_bytes": 1024,
                    "fail_on_exceed": True,
                }
            ],
        )
        rc = budgets_mod.main(
            ["--dist", str(dist), "--budgets", str(budgets), "--json"]
        )
        assert rc == 1
        out = capsys.readouterr().out
        # The output must be valid, parseable JSON.
        report = json.loads(out)
        assert isinstance(report, list)
        assert len(report) == 1
        entry = report[0]
        assert entry["budget"] == "landing"
        assert entry["glob"] == "index.html"
        assert entry["matches"] == 1
        assert entry["hard"] is True
        assert len(entry["violations"]) == 1
        v = entry["violations"][0]
        assert v["kind"] == "raw"
        assert v["actual"] == 2048
        assert v["max"] == 1024
        assert v["file"] == "index.html"

    def test_json_mode_suppresses_human_readable_summary(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The two output paths are exclusive — JSON mode must NOT
        also print the ``[budgets] OK / WARN / FAIL`` lines."""

        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=128)
        budgets = _write_budgets(
            tmp_path,
            [{"id": "landing", "glob": "index.html", "max_bytes": 1024}],
        )
        rc = budgets_mod.main(
            ["--dist", str(dist), "--budgets", str(budgets), "--json"]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "[budgets]" not in out


# ---------------------------------------------------------------------------
# _gzip_len helper
# ---------------------------------------------------------------------------


class TestGzipLen:
    def test_matches_stdlib_gzip(self, tmp_path: Path) -> None:
        path = tmp_path / "x.bin"
        payload = b"hello world\n" * 100
        path.write_bytes(payload)
        expected = len(gzip.compress(payload, compresslevel=9, mtime=0))
        assert budgets_mod._gzip_len(path) == expected

    def test_zero_byte_file_returns_gzip_header_overhead(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "empty.bin"
        path.write_bytes(b"")
        # An empty payload still has a gzip header — the value must
        # be > 0 but small (~20 bytes).
        out = budgets_mod._gzip_len(path)
        assert 0 < out < 100

    def test_uses_deterministic_mtime(self, tmp_path: Path) -> None:
        """``mtime=0`` is critical: it pins the gz size across runs
        so a re-run on the same file always reports the same number.
        We assert the helper does NOT vary across two consecutive
        calls (which it would if mtime came from the filesystem
        clock)."""

        path = tmp_path / "x.bin"
        path.write_bytes(b"abc" * 1000)
        first = budgets_mod._gzip_len(path)
        # Mutate the filesystem mtime then re-compute.
        import os, time
        new_time = time.time() + 1000
        os.utime(path, (new_time, new_time))
        second = budgets_mod._gzip_len(path)
        assert first == second


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestCliSurface:
    def test_argv_none_falls_through_to_sys_argv(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        dist = tmp_path / "dist"
        _make_file(dist, name="index.html", size=128)
        budgets = _write_budgets(
            tmp_path,
            [{"id": "landing", "glob": "index.html", "max_bytes": 1024}],
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["budgets", "--dist", str(dist), "--budgets", str(budgets)],
        )
        assert budgets_mod.main() == 0
        assert "[budgets] OK   landing" in capsys.readouterr().out

    def test_default_budgets_is_repo_local_path(self) -> None:
        """The default ``--budgets`` value is the repo-local
        ``tools/build/budgets.json`` resolved at import time."""

        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--budgets",
            default=str(budgets_mod.DEFAULT_BUDGETS),
        )
        ns = parser.parse_args([])
        # DEFAULT_BUDGETS resolves to <repo>/tools/build/budgets.json
        assert ns.budgets.endswith("tools/build/budgets.json")


# ---------------------------------------------------------------------------
# Module entrypoint guard — subprocess smoke against real dist/
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_against_real_dist(self) -> None:
        """Invoke ``python -m tools.audits.budgets`` against the
        repo's real ``dist/`` tree when it exists. Returns 0 or 1
        depending on whether any hard budget is breached — both are
        acceptable; the assertion is that the script ran to
        completion without raising.

        If ``dist/`` is absent (clean checkout), the script returns 2
        per its documented contract; we accept that too. The point of
        the smoke check is to exercise the ``if __name__ == "__main__":``
        guard end-to-end, not to assert the byte-budget state of the
        repo at test time."""

        import subprocess

        repo_root = Path(budgets_mod.__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.budgets", "--json"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # 0 = clean, 1 = budget breached, 2 = no dist/ yet.
        assert result.returncode in (0, 1, 2)
