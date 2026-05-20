"""Unit tests pinning ``splunk_uc.audits.no_use_cases_dir``.

The audit is the structural guard rail that blocks any reintroduction
of the legacy ``use-cases/`` markdown corpus retired in v8.2.0. It
enforces two invariants:

1. **No directory.** ``use-cases/`` MUST NOT exist under the repo root.
2. **No new path references.** Tracked files MUST NOT contain
   ``use-cases/`` filesystem path references unless the file is on the
   explicit historical/migration ``ALLOWLIST_PATHS``.

Before scanning each line, the audit strips two known-safe substrings:

- ``splunk-monitoring-use-cases`` — the GitHub repo name itself.
- Non-repo external URLs containing ``/use-cases/`` as a third-party
  path component (e.g. ``https://tetragon.io/docs/use-cases/``).

What's left is treated as a real path reference and fails the audit
unless the file is allowlisted.

These tests are hermetic — each one builds a synthetic repo tree under
``tmp_path``, monkey-patches ``nud.REPO_ROOT``, and stubs
``_git_tracked_files`` so the audit operates against the fixture.
"""

from __future__ import annotations

import pathlib
import subprocess
from typing import Protocol

import pytest

from splunk_uc.audits import no_use_cases_dir as nud


class WriteFile(Protocol):
    """Factory protocol for writing a tracked file to the fake repo."""

    def __call__(self, rel: str, body: str) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a fake repo root and rewire ``nud.REPO_ROOT``."""
    monkeypatch.setattr(nud, "REPO_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def write_file(fake_repo: pathlib.Path) -> WriteFile:
    """Return a factory that creates files under the fake repo root."""

    def _make(rel: str, body: str) -> pathlib.Path:
        path = fake_repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    return _make


@pytest.fixture
def stub_tracked_files(
    monkeypatch: pytest.MonkeyPatch, fake_repo: pathlib.Path
) -> list[pathlib.Path]:
    """Stub ``_git_tracked_files`` to return our test fixture set."""
    tracked: list[pathlib.Path] = []

    def _fake() -> list[pathlib.Path]:
        return tracked

    monkeypatch.setattr(nud, "_git_tracked_files", _fake)
    return tracked


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_repo_root_resolves_three_parents_up() -> None:
    """REPO_ROOT resolves to the actual repo root at import time."""
    assert nud.REPO_ROOT.is_absolute()
    assert (nud.REPO_ROOT / "src" / "splunk_uc" / "audits").is_dir()


def test_allowlist_is_frozenset_of_str() -> None:
    """ALLOWLIST_PATHS is a frozenset (immutable contract)."""
    assert isinstance(nud.ALLOWLIST_PATHS, frozenset)
    for entry in nud.ALLOWLIST_PATHS:
        assert isinstance(entry, str)


def test_allowlist_uses_posix_style_paths() -> None:
    """No Windows backslash separators in allowlist entries."""
    for entry in nud.ALLOWLIST_PATHS:
        assert "\\" not in entry


def test_allowlist_includes_documented_governance_files() -> None:
    """Sanity-check known anchors are in the allowlist."""
    assert "CHANGELOG.md" in nud.ALLOWLIST_PATHS
    assert "ROADMAP.md" in nud.ALLOWLIST_PATHS
    assert ".github/CODEOWNERS" in nud.ALLOWLIST_PATHS
    assert "docs/migration-status.md" in nud.ALLOWLIST_PATHS


def test_repo_name_re_matches_github_repo_name() -> None:
    """``splunk-monitoring-use-cases`` is stripped before checking."""
    assert nud._REPO_NAME_RE.sub("", "splunk-monitoring-use-cases/") == ""
    assert (
        nud._REPO_NAME_RE.sub("", "github.com/foo/splunk-monitoring-use-cases/tree/main")
        == "github.com/foo/tree/main"
    )


def test_external_url_re_matches_third_party_use_cases_url() -> None:
    """``https://tetragon.io/docs/use-cases/`` is stripped."""
    line = "See https://tetragon.io/docs/use-cases/foo for context."
    cleaned = nud._EXTERNAL_URL_RE.sub("", line)
    assert "tetragon.io" not in cleaned
    # Note: only the URL prefix up to use-cases/ is matched; trailing
    # path components after use-cases/ remain.
    assert "foo" in cleaned


def test_external_url_re_does_not_match_internal_repo_path() -> None:
    """Plain ``use-cases/`` (no scheme) is NOT matched by the URL regex."""
    line = "use-cases/cat-1-foo.md"
    cleaned = nud._EXTERNAL_URL_RE.sub("", line)
    assert cleaned == line


def test_dir_ref_re_matches_bare_path_reference() -> None:
    """Bare ``use-cases/`` reference triggers the directory check."""
    assert nud._DIR_REF_RE.search("use-cases/cat-foo.md")


def test_dir_ref_re_does_not_match_alphanumeric_prefix() -> None:
    """``X-use-cases/`` (alphanumeric prefix) is NOT a real path ref."""
    assert not nud._DIR_REF_RE.search("phase-use-cases/foo")
    assert not nud._DIR_REF_RE.search("Xuse-cases/")
    assert not nud._DIR_REF_RE.search("9use-cases/")
    # ``_use-cases/`` shouldn't match either.
    assert not nud._DIR_REF_RE.search("_use-cases/")
    # Nor should a literal dot or hyphen prefix.
    assert not nud._DIR_REF_RE.search(".use-cases/")
    assert not nud._DIR_REF_RE.search("-use-cases/")


def test_dir_ref_re_matches_after_whitespace_or_punctuation() -> None:
    """``use-cases/`` after whitespace/punctuation IS a real reference."""
    assert nud._DIR_REF_RE.search(" use-cases/")
    assert nud._DIR_REF_RE.search('"use-cases/')
    assert nud._DIR_REF_RE.search(",use-cases/")
    assert nud._DIR_REF_RE.search("(use-cases/")


# ---------------------------------------------------------------------------
# _git_tracked_files
# ---------------------------------------------------------------------------


def test_git_tracked_files_calls_subprocess(
    fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``_git_tracked_files`` shells out to ``git ls-files`` and returns Paths."""
    captured_cmd: list[list[str]] = []

    def fake_check_output(cmd: list[str], **kwargs: object) -> str:
        captured_cmd.append(cmd)
        return "a.txt\nb.txt\n"

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    result = nud._git_tracked_files()
    assert len(captured_cmd) == 1
    assert captured_cmd[0][:2] == ["git", "-C"]
    assert captured_cmd[0][3:] == ["ls-files"]
    assert all(isinstance(p, pathlib.Path) for p in result)
    assert [p.name for p in result] == ["a.txt", "b.txt"]


def test_git_tracked_files_filters_empty_lines(
    fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty lines from git output are filtered out."""
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **k: "a.txt\n\nb.txt\n\n")
    result = nud._git_tracked_files()
    assert len(result) == 2


# ---------------------------------------------------------------------------
# _scan_file
# ---------------------------------------------------------------------------


def test_scan_file_returns_empty_for_clean_file(write_file: WriteFile) -> None:
    """A file with no ``use-cases/`` references → empty list."""
    path = write_file("clean.txt", "Hello world\nNo references here.")
    assert nud._scan_file(path) == []


def test_scan_file_flags_real_path_reference(write_file: WriteFile) -> None:
    """A bare ``use-cases/`` reference is captured with line number."""
    path = write_file("dirty.txt", "first line\npath: use-cases/cat-1-foo.md\nthird")
    findings = nud._scan_file(path)
    assert findings == [(2, "path: use-cases/cat-1-foo.md")]


def test_scan_file_skips_repo_name(write_file: WriteFile) -> None:
    """``splunk-monitoring-use-cases`` substring is stripped first."""
    path = write_file(
        "repo.md",
        "Clone github.com/user/splunk-monitoring-use-cases\n",
    )
    assert nud._scan_file(path) == []


def test_scan_file_skips_external_url(write_file: WriteFile) -> None:
    """``https://tetragon.io/docs/use-cases/...`` is stripped."""
    path = write_file(
        "url.md",
        "See https://tetragon.io/docs/use-cases/foo for context.\n",
    )
    assert nud._scan_file(path) == []


def test_scan_file_flags_real_ref_alongside_safe_patterns(
    write_file: WriteFile,
) -> None:
    """A safe substring and a real ref on the same line BOTH surface the ref."""
    path = write_file(
        "mixed.md",
        "splunk-monitoring-use-cases plus use-cases/cat-2.md\n",
    )
    findings = nud._scan_file(path)
    assert len(findings) == 1
    assert findings[0][0] == 1


def test_scan_file_handles_oserror(write_file: WriteFile, monkeypatch: pytest.MonkeyPatch) -> None:
    """``OSError`` during read returns an empty list (binary tolerance)."""
    path = write_file("blocked.md", "content")

    def raise_oserror(*args: object, **kwargs: object) -> str:
        raise OSError("no permission")

    monkeypatch.setattr(pathlib.Path, "read_text", raise_oserror)
    assert nud._scan_file(path) == []


def test_scan_file_handles_unicode_decode_error(
    write_file: WriteFile, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``UnicodeDecodeError`` (binary file) returns an empty list."""
    path = write_file("binary.bin", "content")

    def raise_decode(*args: object, **kwargs: object) -> str:
        raise UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte")

    monkeypatch.setattr(pathlib.Path, "read_text", raise_decode)
    assert nud._scan_file(path) == []


def test_scan_file_rstrips_finding_line(write_file: WriteFile) -> None:
    """Captured lines are rstripped (trailing whitespace removed)."""
    path = write_file("trailing.txt", "use-cases/foo   \n")
    findings = nud._scan_file(path)
    assert findings == [(1, "use-cases/foo")]


def test_scan_file_returns_multiple_findings(write_file: WriteFile) -> None:
    """A file with multiple offending lines returns one finding per line."""
    path = write_file(
        "multi.md",
        "use-cases/a.md\n# comment\nuse-cases/b.md\n",
    )
    findings = nud._scan_file(path)
    assert len(findings) == 2
    assert findings[0][0] == 1
    assert findings[1][0] == 3


# ---------------------------------------------------------------------------
# _check_directory_absent
# ---------------------------------------------------------------------------


def test_check_directory_absent_returns_empty_when_missing(
    fake_repo: pathlib.Path,
) -> None:
    """No ``use-cases/`` dir → no issues."""
    assert nud._check_directory_absent() == []


def test_check_directory_absent_flags_directory_when_present(
    fake_repo: pathlib.Path,
) -> None:
    """If ``use-cases/`` reappears, surface a FATAL line."""
    (fake_repo / "use-cases").mkdir()
    issues = nud._check_directory_absent()
    assert len(issues) == 1
    assert "FATAL" in issues[0]
    assert "v8.2.0" in issues[0]
    assert "docs/migration-status.md" in issues[0]


def test_check_directory_absent_handles_file_at_use_cases_path(
    fake_repo: pathlib.Path,
) -> None:
    """A ``use-cases`` FILE (not dir) also trips the guard (Path.exists)."""
    (fake_repo / "use-cases").write_text("legacy", encoding="utf-8")
    issues = nud._check_directory_absent()
    assert len(issues) == 1


# ---------------------------------------------------------------------------
# _check_path_references
# ---------------------------------------------------------------------------


def test_check_path_references_returns_empty_when_clean(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Clean repo → no path-reference issues."""
    path = write_file("clean.txt", "no references\n")
    stub_tracked_files.append(path)
    assert nud._check_path_references() == []


def test_check_path_references_flags_unlisted_file(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """A non-allowlisted file with ``use-cases/`` ref surfaces an issue."""
    path = write_file("not-allowed.md", "path: use-cases/cat-1.md\n")
    stub_tracked_files.append(path)
    issues = nud._check_path_references()
    assert len(issues) == 1
    assert "not-allowed.md:1:" in issues[0]


def test_check_path_references_skips_allowlisted_file(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Allowlisted file with ``use-cases/`` ref is silently skipped."""
    path = write_file("CHANGELOG.md", "Refers to use-cases/legacy.md\n")
    stub_tracked_files.append(path)
    assert nud._check_path_references() == []


def test_check_path_references_skips_dist_subtree(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Files under ``dist/`` are skipped (generated artefacts)."""
    path = write_file("dist/generated.md", "use-cases/cat-1.md\n")
    stub_tracked_files.append(path)
    assert nud._check_path_references() == []


def test_check_path_references_skips_directory_entry(
    fake_repo: pathlib.Path,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Non-file entries (directories) in tracked-files output are skipped."""
    sub_dir = fake_repo / "subdir"
    sub_dir.mkdir()
    stub_tracked_files.append(sub_dir)
    assert nud._check_path_references() == []


def test_check_path_references_truncates_long_snippet(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Snippets longer than 140 chars are truncated with ``...`` suffix."""
    long_line = "use-cases/" + "x" * 200
    path = write_file("long.md", f"{long_line}\n")
    stub_tracked_files.append(path)
    issues = nud._check_path_references()
    assert len(issues) == 1
    # Issue format: "{rel_posix}:{line_no}: {snippet}"
    # split(": ", 1) → ["long.md:1", snippet]
    issue = issues[0]
    snippet = issue.split(": ", 1)[1]
    assert len(snippet) == 140
    assert snippet.endswith("...")


def test_check_path_references_does_not_truncate_short_snippet(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Snippets ≤140 chars are NOT truncated."""
    short_line = "use-cases/cat-1.md"
    path = write_file("short.md", f"{short_line}\n")
    stub_tracked_files.append(path)
    issues = nud._check_path_references()
    assert len(issues) == 1
    assert not issues[0].endswith("...")


def test_check_path_references_strips_leading_whitespace_in_snippet(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """The snippet is left-stripped before truncation/formatting."""
    path = write_file("indented.md", "    use-cases/x.md\n")
    stub_tracked_files.append(path)
    issues = nud._check_path_references()
    assert len(issues) == 1
    issue = issues[0]
    snippet = issue.split(": ", 1)[1]
    assert snippet == "use-cases/x.md"


def test_check_path_references_includes_relative_posix_path(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """Issue strings use posix-style relative paths."""
    path = write_file("nested/file.md", "use-cases/a.md\n")
    stub_tracked_files.append(path)
    issues = nud._check_path_references()
    assert issues[0].startswith("nested/file.md:")


# ---------------------------------------------------------------------------
# _print_allowlist
# ---------------------------------------------------------------------------


def test_print_allowlist_prints_header_and_entries(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``_print_allowlist`` prints documented header + sorted entries."""
    nud._print_allowlist()
    captured = capsys.readouterr()
    assert "# use-cases/ historical-reference allowlist" in captured.out
    assert "CHANGELOG.md" in captured.out
    # Verify sorted order is preserved.
    lines = captured.out.splitlines()
    # Header comments start with '#'; entries don't.
    entries = [line for line in lines if line and not line.startswith("#")]
    assert entries == sorted(entries)


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_returns_0_when_clean(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Clean repo → exit 0 with success message."""
    path = write_file("clean.txt", "no refs here\n")
    stub_tracked_files.append(path)
    assert nud.main([]) == 0
    captured = capsys.readouterr()
    assert "OK: no use-cases/ directory and no stray path references" in captured.out
    assert f"({len(nud.ALLOWLIST_PATHS)} historical files allowlisted)" in captured.out


def test_main_returns_2_when_directory_present(
    fake_repo: pathlib.Path,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reappeared ``use-cases/`` dir → exit 2."""
    (fake_repo / "use-cases").mkdir()
    assert nud.main([]) == 2
    captured = capsys.readouterr()
    assert "Legacy use-cases/ guard found violations:" in captured.out
    assert "FATAL" in captured.out


def test_main_returns_2_when_unlisted_ref_present(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unlisted file with a real ref → exit 2."""
    path = write_file("not-allowed.md", "see use-cases/foo.md\n")
    stub_tracked_files.append(path)
    assert nud.main([]) == 2
    captured = capsys.readouterr()
    assert "Total: 1 violation(s)" in captured.out


def test_main_check_flag_accepted_as_alias(
    fake_repo: pathlib.Path,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """``--check`` is accepted as a no-op alias for default behaviour."""
    assert nud.main(["--check"]) == 0


def test_main_argv_none_uses_sys_argv_default(
    fake_repo: pathlib.Path,
    stub_tracked_files: list[pathlib.Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-no-use-cases-dir"])
    assert nud.main(None) == 0


def test_main_help_exits_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits 0 with documented flags."""
    with pytest.raises(SystemExit) as exc:
        nud.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--check" in captured.out
    assert "--list-allowlist" in captured.out


# ---------------------------------------------------------------------------
# main() — --list-allowlist
# ---------------------------------------------------------------------------


def test_main_list_allowlist_returns_0_and_prints(
    fake_repo: pathlib.Path,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--list-allowlist`` exits 0 and prints the allowlist."""
    assert nud.main(["--list-allowlist"]) == 0
    captured = capsys.readouterr()
    assert "# use-cases/ historical-reference allowlist" in captured.out
    assert "CHANGELOG.md" in captured.out


def test_main_list_allowlist_does_not_run_path_check(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
) -> None:
    """``--list-allowlist`` short-circuits before the path-reference walk.

    Even if a violating file exists, the audit returns 0 because
    the path-reference walk is never invoked.
    """
    path = write_file("violation.md", "use-cases/x.md\n")
    stub_tracked_files.append(path)
    assert nud.main(["--list-allowlist"]) == 0


# ---------------------------------------------------------------------------
# main() — violation reporting
# ---------------------------------------------------------------------------


def test_main_violation_message_includes_advice(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Violation message includes the canonical "Either remove..." advice."""
    path = write_file("bad.md", "use-cases/x.md\n")
    stub_tracked_files.append(path)
    assert nud.main([]) == 2
    captured = capsys.readouterr()
    assert "Either remove the reference" in captured.out
    assert "ALLOWLIST_PATHS" in captured.out
    assert "src/splunk_uc/audits/no_use_cases_dir.py" in captured.out


def test_main_multiple_violations_listed_individually(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Multiple violations each surface as their own bullet."""
    path_a = write_file("a.md", "use-cases/foo.md\n")
    path_b = write_file("b.md", "use-cases/bar.md\n")
    stub_tracked_files.extend([path_a, path_b])
    assert nud.main([]) == 2
    captured = capsys.readouterr()
    assert "Total: 2 violation(s)" in captured.out


def test_main_combines_dir_and_path_violations(
    fake_repo: pathlib.Path,
    write_file: WriteFile,
    stub_tracked_files: list[pathlib.Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Directory check AND path-ref check both contribute to the total."""
    (fake_repo / "use-cases").mkdir()
    path = write_file("ref.md", "use-cases/cat-1.md\n")
    stub_tracked_files.append(path)
    assert nud.main([]) == 2
    captured = capsys.readouterr()
    assert "Total: 2 violation(s)" in captured.out
    assert "FATAL" in captured.out
