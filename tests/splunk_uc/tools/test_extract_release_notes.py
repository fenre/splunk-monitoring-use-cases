"""Hermetic coverage suite for ``splunk_uc.tools.extract_release_notes``.

The release-notes extractor runs in the release workflow and writes
the body of the GitHub Release page. A regression here silently
ships an empty / wrong-version notes page, so the suite pins every
branch of the CLI surface.

Lifts coverage from 22.7% to 100%. Real CHANGELOG.md is monkeypatched
to a tmp_path copy so the suite stays hermetic.
"""

from __future__ import annotations

import pathlib

import pytest

from splunk_uc.tools import extract_release_notes as ern


@pytest.fixture
def fake_changelog(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n"
        "\n"
        "## [1.2.0] - 2026-05-01\n"
        "\n"
        "Released the foo feature.\n"
        "\n"
        "- Added bar\n"
        "- Removed baz\n"
        "\n"
        "## [1.1.0] - 2026-04-01\n"
        "\n"
        "Earlier release.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ern, "CHANGELOG", changelog)
    return changelog


class TestExtractSection:
    def test_returns_body_for_matching_version(
        self, fake_changelog: pathlib.Path
    ) -> None:
        body = ern.extract_section("1.2.0")
        assert body is not None
        assert "Released the foo feature." in body
        assert "Added bar" in body
        # The body must end with a trailing newline.
        assert body.endswith("\n")
        # And it must NOT spill into the 1.1.0 section.
        assert "Earlier release." not in body

    def test_returns_none_for_unknown_version(
        self, fake_changelog: pathlib.Path
    ) -> None:
        assert ern.extract_section("9.9.9") is None

    def test_returns_none_when_changelog_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
    ) -> None:
        monkeypatch.setattr(ern, "CHANGELOG", tmp_path / "nope.md")
        assert ern.extract_section("1.2.0") is None

    def test_handles_special_regex_chars_in_version(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
    ) -> None:
        # The version is escaped with re.escape so a literal dot in the
        # version string doesn't unintentionally match arbitrary chars.
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "## [1.2.0-rc.1] - 2026-05-15\n\nRC body.\n", encoding="utf-8"
        )
        monkeypatch.setattr(ern, "CHANGELOG", changelog)
        body = ern.extract_section("1.2.0-rc.1")
        assert body is not None
        assert "RC body." in body


class TestBuildBody:
    def test_appends_boilerplate_to_extracted_section(
        self, fake_changelog: pathlib.Path
    ) -> None:
        body = ern.build_body("1.2.0")
        assert "Released the foo feature." in body
        assert "TA-splunk-use-cases-1.2.0.spl" in body
        assert "DA-ITSI-monitoring-use-cases-1.2.0.spl" in body
        assert "DA-ESS-monitoring-use-cases-1.2.0.spl" in body

    def test_falls_back_to_minimal_section_when_version_missing(
        self, fake_changelog: pathlib.Path
    ) -> None:
        body = ern.build_body("9.9.9")
        assert "## 9.9.9" in body
        assert "documented in [CHANGELOG.md](CHANGELOG.md)" in body
        # Boilerplate still gets appended even for fallback sections.
        assert "TA-splunk-use-cases-9.9.9.spl" in body


class TestMain:
    def test_prints_usage_with_rc_2_when_no_args(
        self, capsys: pytest.CaptureFixture[str], fake_changelog: pathlib.Path
    ) -> None:
        rc = ern.main([])
        assert rc == 2
        assert "usage:" in capsys.readouterr().err

    def test_writes_body_to_stdout_when_no_output_path(
        self, capsys: pytest.CaptureFixture[str], fake_changelog: pathlib.Path
    ) -> None:
        rc = ern.main(["1.2.0"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Released the foo feature." in out
        assert "TA-splunk-use-cases-1.2.0.spl" in out

    def test_writes_body_to_file_when_output_path_given(
        self,
        capsys: pytest.CaptureFixture[str],
        fake_changelog: pathlib.Path,
        tmp_path: pathlib.Path,
    ) -> None:
        target = tmp_path / "build" / "release-notes.md"
        rc = ern.main(["1.2.0", str(target)])
        assert rc == 0
        assert target.exists()
        body = target.read_text(encoding="utf-8")
        assert "Released the foo feature." in body
        # The "wrote …" log line goes to stdout.
        assert "wrote" in capsys.readouterr().out

    def test_consumes_sys_argv_when_argv_omitted(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fake_changelog: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Force sys.argv to look like a CLI invocation; main() with
        # argv=None should pick it up.
        monkeypatch.setattr(ern.sys, "argv", ["extract-release-notes", "1.2.0"])
        rc = ern.main(None)
        assert rc == 0
        assert "Released the foo feature." in capsys.readouterr().out
