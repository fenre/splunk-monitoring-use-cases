"""Hermetic tests for the legacy repo-root ``./validate_md.py``.

Status
------

``./validate_md.py`` is the v6-era markdown validator that targeted
the legacy ``use-cases/`` directory. The v7 catalogue migrated to
per-UC JSON sidecars under ``content/`` and the canonical validator
is now ``tools/validate/validate_md.py`` (the latter is at 100%
line + branch coverage already).

The repo-root validator is:

* NOT invoked from CI (.github/workflows/*.yml) — confirmed via
  repo-wide grep.
* NOT invoked from the Makefile — confirmed via repo-wide grep.
* Logically broken: it reads from ``use-cases/`` which is now
  forbidden by ``src/splunk_uc/audits/no_use_cases_dir.py`` (any
  attempt to recreate that directory fails the audit gate).

We keep the file in the tree (and at 100% line + branch coverage)
to preserve the v6 contract for downstream forks that haven't
migrated yet AND so that we can detect drift (e.g. someone trying
to re-add a ``use-cases/`` directory) via a tripwire test.

Hermetic isolation
------------------

The tests use ``tmp_path`` and ``monkeypatch`` to swap the
module's ``USE_CASES_DIR`` to a synthetic fixture directory. No
real ``use-cases/`` is created or consumed.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def validate_md():
    """Load the legacy ./validate_md.py via importlib.

    We deliberately use ``spec_from_file_location`` instead of
    ``import validate_md`` because:

    1. The repo root isn't on ``sys.path`` during pytest runs
       (only ``src/`` and ``mcp/src/`` are configured via
       ``pyproject.toml`` ``pythonpath``).
    2. A bare ``import validate_md`` would also collide with the
       canonical ``tools/validate/validate_md.py`` if both were
       reachable on PYTHONPATH.

    Loading by path keeps this test hermetic and scoped to the
    legacy file.
    """
    spec = importlib.util.spec_from_file_location(
        "validate_md_legacy", REPO_ROOT / "validate_md.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# validate_file
# ---------------------------------------------------------------------------


class TestValidateFileSkip:
    def test_skipped_files_return_empty(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 11-12: the SKIP set returns empty errors/warnings without
        even opening the file."""
        path = tmp_path / "cat-00-preamble.md"
        # Deliberately do NOT write content — the SKIP branch returns
        # before the open() call. If we get past that branch this
        # test will FileNotFoundError instead of passing.
        errs, warns = validate_md.validate_file(str(path))
        assert errs == []
        assert warns == []


class TestValidateFileCategoryHeading:
    def test_missing_category_heading_reports_error(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 22-23: a file without ``# N. ...`` or ``## N. ...``
        returns a single category-heading error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text("No heading here.\nJust prose.\n", encoding="utf-8")
        errs, warns = validate_md.validate_file(str(path))
        assert len(errs) == 1
        assert errs[0][0] == str(path)
        assert "no category heading" in errs[0][1]
        assert warns == []

    def test_present_category_heading_continues(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Cover the True arm at line 22: heading present → continue
        to the rest of the validation pipeline (no early return)."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text("# 1. Category\n", encoding="utf-8")
        errs, warns = validate_md.validate_file(str(path))
        assert errs == []
        assert warns == []


class TestValidateFileUcIdMismatch:
    def test_uc_id_with_wrong_category_reports_error(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 28-30: every UC-ID in the markdown that doesn't
        start with the file's category number triggers an error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n### UC-2.1.1 · Wrong-category UC\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert any(
            "UC-ID 2.1.1 does not match category 1" in msg for _, msg in errs
        )

    def test_uc_id_matching_category_passes(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 28-30 — False arm: matching UC-ID passes the loop."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n### UC-1.1.1 · Right-category UC\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert errs == []


class TestValidateFileCodeBlockBalance:
    def test_odd_backticks_reports_error(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 34-35: odd number of ``` lines is an unclosed-code-block
        error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n```\nopen but never closed\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert any("odd number of ``` lines" in msg for _, msg in errs)

    def test_even_backticks_passes(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Cover the False arm at line 34: even ``` count → no error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n```\nbalanced\n```\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert errs == []


class TestValidateFileLineByLineLoop:
    def test_uc_subcategory_mismatch_reports_error(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 44-49: a UC-line with a subcategory that doesn't
        start with the category number triggers a per-line error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n### UC-2.1.5 · Wrong subcategory\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        # Both the global UC-ID check (lines 28-30) and the
        # per-line check (lines 44-49) fire on this fixture.
        assert any(
            "UC subcategory 2.1 doesn't match category 1" in msg for _, msg in errs
        )

    def test_uc_subcategory_matching_passes_per_line(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Cover the False arm at line 48: matching UC subcategory
        leaves the line loop quiet."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n### UC-1.2.3 · Right subcategory\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert errs == []

    def test_subcat_heading_mismatch_reports_error(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Lines 50-54: a subcategory heading (``## 1.1`` or
        ``### 1.1``) whose number doesn't start with the category
        number triggers a per-line error."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n## 2.1 Wrong subcategory heading\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert any(
            "subcategory 2.1 doesn't match category 1" in msg for _, msg in errs
        )

    def test_subcat_heading_matching_passes(
        self, tmp_path: Path, validate_md
    ) -> None:
        """Cover the False arm at line 53: matching subcategory
        heading number leaves the loop quiet."""
        path = tmp_path / "cat-01-foo.md"
        path.write_text(
            "# 1. Foo\n\n## 1.1 Right subcategory heading\n",
            encoding="utf-8",
        )
        errs, _ = validate_md.validate_file(str(path))
        assert errs == []


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_use_cases_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, validate_md
) -> Path:
    """Point the module's USE_CASES_DIR at a synthetic dir per test."""
    monkeypatch.setattr(validate_md, "USE_CASES_DIR", str(tmp_path))
    return tmp_path


class TestMain:
    def test_main_returns_zero_when_no_errors(
        self, fake_use_cases_dir: Path, capsys: pytest.CaptureFixture, validate_md
    ) -> None:
        """Lines 68-73: clean walk → main returns 0 and prints the
        success banner."""
        (fake_use_cases_dir / "cat-01-foo.md").write_text(
            "# 1. Foo\n\n### UC-1.1.1 · OK\n",
            encoding="utf-8",
        )
        rc = validate_md.main()
        out = capsys.readouterr().out
        assert rc == 0
        assert "Validation passed" in out

    def test_main_returns_one_when_errors(
        self, fake_use_cases_dir: Path, capsys: pytest.CaptureFixture, validate_md
    ) -> None:
        """Lines 68-71: any error → main prints per-error lines and
        returns 1."""
        bad = fake_use_cases_dir / "cat-01-foo.md"
        bad.write_text(
            "no heading at all\n",
            encoding="utf-8",
        )
        rc = validate_md.main()
        out = capsys.readouterr().out
        assert rc == 1
        assert "no category heading" in out
        assert str(bad) in out

    def test_main_skips_non_cat_files(
        self, fake_use_cases_dir: Path, validate_md
    ) -> None:
        """Lines 61-62: files that don't start with ``cat-`` or
        don't end in ``.md`` are skipped before validate_file is
        called."""
        # README.md doesn't start with ``cat-`` → skip.
        (fake_use_cases_dir / "README.md").write_text(
            "no heading\n", encoding="utf-8"
        )
        # cat-99-foo.txt doesn't end in ``.md`` → skip.
        (fake_use_cases_dir / "cat-99-foo.txt").write_text(
            "no heading\n", encoding="utf-8"
        )
        # Without any cat-*.md files we expect a clean pass.
        rc = validate_md.main()
        assert rc == 0

    def test_main_skips_directories(
        self, fake_use_cases_dir: Path, validate_md
    ) -> None:
        """Lines 64-65: a directory matching ``cat-*.md`` (unusual
        but possible) is skipped via the ``isfile`` guard."""
        weird = fake_use_cases_dir / "cat-99-folder.md"
        weird.mkdir()
        rc = validate_md.main()
        assert rc == 0


# ---------------------------------------------------------------------------
# __name__ == "__main__" guard
# ---------------------------------------------------------------------------


class TestMainGuard:
    def test_main_guard_invokes_main_via_runpy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Cover the ``if __name__ == "__main__":`` block by
        running the script through ``runpy.run_path`` with a
        synthetic, empty USE_CASES_DIR. The script returns 0 via
        ``exit()`` which raises ``SystemExit(0)``."""
        # Copy the script into a temp location with an adjacent
        # use-cases/ dir so the synthetic USE_CASES_DIR exists.
        import runpy
        import shutil

        script = REPO_ROOT / "validate_md.py"
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        shutil.copy(script, fake_repo / "validate_md.py")
        (fake_repo / "use-cases").mkdir()
        sys.path.insert(0, str(fake_repo))
        try:
            with pytest.raises(SystemExit) as excinfo:
                runpy.run_path(
                    str(fake_repo / "validate_md.py"),
                    run_name="__main__",
                )
            # ``exit(0)`` raises SystemExit with code 0 — clean pass.
            assert excinfo.value.code == 0
        finally:
            sys.path.remove(str(fake_repo))
