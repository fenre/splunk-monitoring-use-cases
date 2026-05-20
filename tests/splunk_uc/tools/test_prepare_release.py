"""Hermetic coverage suite for ``splunk_uc.tools.prepare_release``.

The release-prep CLI is the gate that pins ``VERSION`` ↔ ``CHANGELOG.md``
↔ ``index.html`` ↔ ``CITATION.cff`` ↔ ``openapi.yaml`` consistency.
It is invoked from ``Makefile`` and the GitHub Actions release workflow,
so a regression here can ship a release with one of the five files
pointing at the wrong version.

Module-level constants point at the live repo files; every test
monkeypatches them onto tmp_path copies so the suite stays hermetic.
Brings coverage from 23.6% to 100%.
"""

from __future__ import annotations

import pathlib

import pytest

from splunk_uc.tools import prepare_release as pr


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Stage a fake repo root with all five tracked files at version 7.4.0."""
    (tmp_path / "VERSION").write_text("7.4.0\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [7.4.0] - 2026-05-20\n\nRelease body.\n",
        encoding="utf-8",
    )
    (tmp_path / "CITATION.cff").write_text(
        'cff-version: "1.2.0"\ntitle: "Splunk UC"\nversion: "7.4.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "openapi.yaml").write_text(
        'openapi: 3.0.3\ninfo:\n  title: x\n  version: "7.4.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "index.html").write_text(
        "<html><body>v7.4.0 release notes</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(pr, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(pr, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(pr, "CHANGELOG", tmp_path / "CHANGELOG.md")
    monkeypatch.setattr(pr, "INDEX_HTML", tmp_path / "index.html")
    monkeypatch.setattr(pr, "CITATION", tmp_path / "CITATION.cff")
    monkeypatch.setattr(pr, "OPENAPI", tmp_path / "openapi.yaml")
    return tmp_path


class TestReadVersion:
    def test_returns_trimmed_contents(self, fake_repo: pathlib.Path) -> None:
        assert pr.read_version() == "7.4.0"


class TestCheckChangelog:
    def test_returns_none_when_header_present(self, fake_repo: pathlib.Path) -> None:
        assert pr.check_changelog("7.4.0") is None

    def test_returns_error_when_header_missing(self, fake_repo: pathlib.Path) -> None:
        err = pr.check_changelog("9.9.9")
        assert err is not None
        assert "missing ## [9.9.9]" in err

    def test_special_chars_in_version_are_escaped(
        self, fake_repo: pathlib.Path
    ) -> None:
        (fake_repo / "CHANGELOG.md").write_text(
            "## [7.4.0-rc.1] - 2026-05-20\n", encoding="utf-8"
        )
        assert pr.check_changelog("7.4.0-rc.1") is None
        assert pr.check_changelog("7.4.0") is not None


class TestCheckCitation:
    def test_returns_none_when_version_present(self, fake_repo: pathlib.Path) -> None:
        assert pr.check_citation("7.4.0") is None

    def test_returns_error_when_version_missing(self, fake_repo: pathlib.Path) -> None:
        err = pr.check_citation("9.9.9")
        assert err is not None
        assert "version field does not match 9.9.9" in err


class TestCheckOpenapi:
    def test_returns_none_when_version_present(self, fake_repo: pathlib.Path) -> None:
        assert pr.check_openapi("7.4.0") is None

    def test_returns_error_when_version_missing(self, fake_repo: pathlib.Path) -> None:
        err = pr.check_openapi("9.9.9")
        assert err is not None
        assert "info.version does not start with 9.9.9" in err

    def test_matches_prefix_not_exact(self, fake_repo: pathlib.Path) -> None:
        # The helper checks for ``version: "<ver>`` prefix, so a longer
        # tagged version (e.g. 7.4.0-beta) still matches the 7.4.0 prefix.
        (fake_repo / "openapi.yaml").write_text(
            'openapi: 3.0.3\ninfo:\n  version: "7.4.0-beta"\n',
            encoding="utf-8",
        )
        assert pr.check_openapi("7.4.0") is None


class TestCheckIndexHtml:
    @pytest.mark.parametrize(
        "marker_text",
        [
            "<div>v7.4.0</div>",
            "<p>Version 7.4.0 release notes</p>",
            "## [7.4.0] - released",
        ],
    )
    def test_returns_none_for_any_supported_marker(
        self, fake_repo: pathlib.Path, marker_text: str
    ) -> None:
        (fake_repo / "index.html").write_text(marker_text, encoding="utf-8")
        assert pr.check_index_html("7.4.0") is None

    def test_returns_error_when_no_marker_present(
        self, fake_repo: pathlib.Path
    ) -> None:
        (fake_repo / "index.html").write_text(
            "<html>nothing here</html>", encoding="utf-8"
        )
        err = pr.check_index_html("7.4.0")
        assert err is not None
        assert "no reference to version 7.4.0" in err


class TestMain:
    def test_passes_when_all_files_consistent(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = pr.main([])
        assert rc == 0
        assert "Release check PASSED" in capsys.readouterr().out

    def test_check_mode_returns_1_on_drift(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Bump VERSION so the other files drift out.
        (fake_repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        rc = pr.main(["--check"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "Release check FAILED for version 9.9.9" in captured.err
        # All four file checks should have failed.
        for token in ("CHANGELOG.md", "CITATION.cff", "openapi.yaml", "index.html"):
            assert token in captured.err

    def test_drift_without_check_flag_still_returns_0(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Without --check, drift is surfaced via stderr but rc=0 so
        # callers can use the script to *see* drift in a soft mode.
        (fake_repo / "VERSION").write_text("9.9.9\n", encoding="utf-8")
        rc = pr.main([])
        assert rc == 0
        captured = capsys.readouterr()
        assert "Release check FAILED for version 9.9.9" in captured.err

    def test_version_flag_writes_version_file(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = pr.main(["--version", "8.0.0"])
        assert rc == 0
        assert (fake_repo / "VERSION").read_text(encoding="utf-8") == "8.0.0\n"
        out = capsys.readouterr().out
        assert "VERSION set to 8.0.0" in out
        assert "must be updated manually" in out

    def test_help_text_does_not_crash_when_docstring_blank(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Pin the ``if __doc__ else None`` branch by erasing the module
        # docstring before argparse pulls the description.
        monkeypatch.setattr(pr, "__doc__", None)
        with pytest.raises(SystemExit) as excinfo:
            pr.main(["--help"])
        assert excinfo.value.code == 0
