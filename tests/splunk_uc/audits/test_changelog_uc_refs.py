"""Hermetic unit tests for ``splunk_uc.audits.changelog_uc_refs``.

P16 wave XX (2026-05-19). Two-faced quality check:

1. CHANGELOG.md version-header parsing: shape, dates, duplicates,
   ordering (monotonically non-increasing dates top-to-bottom).
2. UC cross-references: every ``UC-X.Y.Z`` mentioned in CHANGELOG.md
   must resolve to a real sidecar under ``content/cat-*/UC-*.json``.

Tests pin every documented contract:

* Module-level constants (``REPO`` walks 3 parents up; ``CHANGELOG``
  is at the repo root; ``CONTENT`` is the JSON SSOT path); ``HEADER_RE``
  matches the ``## [ver] - rest`` shape; ``UC_REF_RE`` matches
  ``UC-X.Y.Z`` between word boundaries.
* ``ChangelogEntry`` dataclass (5 fields).
* ``parse_changelog`` matrix (missing file → issue + empty entries;
  malformed header line skipped; ISO range syntax accepted; non-ISO
  with fallback date parsed; no date at all → issue; out-of-calendar
  date → ValueError caught; date-range with invalid first date →
  ValueError caught; shape mismatch on a date-only header → issue).
* ``validate_changelog`` matrix (duplicates flagged with line numbers;
  out-of-order dates flagged; missing dates skipped from ordering check).
* ``collect_uc_definitions`` matrix (clean dict → UC ID added with
  ``UC-`` prefix; malformed JSON → issue with relative path; missing
  ``id`` field skipped; non-string ``id`` stringified then matched
  against pattern; non-canonical ``id`` like ``foo`` skipped via
  regex filter).
* ``validate_uc_refs`` matrix (missing CHANGELOG → empty issues;
  every UC ref in changelog checked; valid refs not flagged; unknown
  refs surface with line number and snippet; multiple refs per line
  all surfaced).
* ``main()`` matrix: 0 on clean, 1 on any issue; entries-summary
  block prints first 5 with ``... (N more)``; ``--help`` exits 0;
  ``argv=None`` falls through to ``sys.argv``.
"""

from __future__ import annotations

import json
import pathlib
from datetime import date
from typing import Any, Protocol

import pytest

import splunk_uc.audits.changelog_uc_refs as cur


# ----------------------------------------------------------- module constants --
def test_repo_walks_three_parents_up() -> None:
    here = pathlib.Path(cur.__file__).resolve()
    assert cur.REPO == here.parents[3]


def test_changelog_path_constant() -> None:
    assert cur.CHANGELOG == cur.REPO / "CHANGELOG.md"


def test_content_path_constant() -> None:
    assert cur.CONTENT == cur.REPO / "content"


def test_header_re_matches_documented_shape() -> None:
    m = cur.HEADER_RE.match("## [9.1.0] - 2026-05-19")
    assert m is not None
    assert m.group("ver") == "9.1.0"
    assert m.group("rest") == "2026-05-19"
    # An ISO range using an EN DASH separator is captured verbatim too.
    m2 = cur.HEADER_RE.match("## [9.1.0] - 2026-05-19 \u2013 2026-05-20")
    assert m2 is not None
    assert "2026-05-19" in m2.group("rest")


def test_header_re_rejects_non_h2() -> None:
    assert cur.HEADER_RE.match("# [9.0.0] - 2026-05-18") is None
    assert cur.HEADER_RE.match("### [9.0.0] - 2026-05-18") is None
    # Empty version not accepted
    assert cur.HEADER_RE.match("## []  -  2026-05-18") is None


def test_uc_ref_re_matches_word_bounded() -> None:
    assert cur.UC_REF_RE.findall("see UC-22.1.1 for details") == ["UC-22.1.1"]
    # multi-segment UC ID
    assert cur.UC_REF_RE.findall("UC-1.2.3 and UC-22.1.99") == [
        "UC-1.2.3",
        "UC-22.1.99",
    ]
    # word boundary stops at the trailing 'x'
    assert cur.UC_REF_RE.findall("UC-1.2.3xx") == []
    # leading non-word char allowed
    assert cur.UC_REF_RE.findall("`UC-1.2.3`") == ["UC-1.2.3"]


def test_changelog_entry_dataclass_shape() -> None:
    e = cur.ChangelogEntry(
        line=1,
        version="9.1.0",
        date_raw="2026-05-19",
        date_parsed=date(2026, 5, 19),
        line_text="## [9.1.0] - 2026-05-19",
    )
    assert e.line == 1
    assert e.version == "9.1.0"
    assert e.date_raw == "2026-05-19"
    assert e.date_parsed == date(2026, 5, 19)
    assert e.line_text == "## [9.1.0] - 2026-05-19"


# ---------------------------------------------------------------- fixtures ----
class WriteChangelog(Protocol):
    def __call__(self, body: str) -> None: ...


class WriteUC(Protocol):
    def __call__(
        self,
        cat: str,
        uc_id: str,
        body: Any = ...,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Synthetic repo root patched into ``REPO``/``CHANGELOG``/``CONTENT``."""
    (tmp_path / "content").mkdir()
    monkeypatch.setattr(cur, "REPO", tmp_path)
    monkeypatch.setattr(cur, "CHANGELOG", tmp_path / "CHANGELOG.md")
    monkeypatch.setattr(cur, "CONTENT", tmp_path / "content")
    return tmp_path


@pytest.fixture
def write_changelog(fake_repo: pathlib.Path) -> WriteChangelog:
    def _factory(body: str) -> None:
        cur.CHANGELOG.write_text(body, encoding="utf-8")

    return _factory


@pytest.fixture
def write_uc(fake_repo: pathlib.Path) -> WriteUC:
    def _factory(
        cat: str,
        uc_id: str,
        body: Any = ...,
    ) -> pathlib.Path:
        cat_dir: pathlib.Path = cur.CONTENT / cat
        cat_dir.mkdir(exist_ok=True)
        p: pathlib.Path = cat_dir / f"UC-{uc_id}.json"
        if body is ...:
            body = {"id": uc_id}
        if isinstance(body, str):
            p.write_text(body, encoding="utf-8")
        else:
            p.write_text(json.dumps(body), encoding="utf-8")
        return p

    return _factory


# ----------------------------------------------------------- parse_changelog --
def test_parse_changelog_missing_file_issues(fake_repo: pathlib.Path) -> None:
    entries, issues = cur.parse_changelog()
    assert entries == []
    assert any("CHANGELOG.md not found" in i for i in issues)


def test_parse_changelog_iso_date_parsed(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("## [9.1.0] - 2026-05-19\n")
    entries, issues = cur.parse_changelog()
    assert issues == []
    assert len(entries) == 1
    assert entries[0].version == "9.1.0"
    assert entries[0].date_parsed == date(2026, 5, 19)


def test_parse_changelog_iso_range_accepted(
    write_changelog: WriteChangelog,
) -> None:
    """ISO date range with hyphen separator parses the first date."""
    write_changelog("## [9.1.0] - 2026-05-19 - 2026-05-20\n")
    entries, _ = cur.parse_changelog()
    assert entries[0].date_parsed == date(2026, 5, 19)


def test_parse_changelog_iso_range_with_en_dash(
    write_changelog: WriteChangelog,
) -> None:
    """ISO date range with EN DASH separator (U+2013) parses too."""
    write_changelog("## [9.1.0] - 2026-05-19 \u2013 2026-05-20\n")
    entries, issues = cur.parse_changelog()
    assert entries[0].date_parsed == date(2026, 5, 19)
    assert issues == []


def test_parse_changelog_non_iso_with_fallback_date(
    write_changelog: WriteChangelog,
) -> None:
    """Non-ISO ``rest`` but a YYYY-MM-DD embedded → parsed by fallback regex."""
    write_changelog("## [9.1.0] - Release Day 2026-05-19 (Spring Hackathon)\n")
    entries, issues = cur.parse_changelog()
    assert entries[0].date_parsed == date(2026, 5, 19)
    assert issues == []


def test_parse_changelog_no_date_in_header_flags_issue(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("## [9.1.0] - This is not a date\n")
    entries, issues = cur.parse_changelog()
    assert any("No YYYY-MM-DD date found" in i for i in issues)
    assert entries[0].date_parsed is None


def test_parse_changelog_invalid_iso_date_caught(
    write_changelog: WriteChangelog,
) -> None:
    """Calendar-invalid date like 2026-02-31 → ValueError caught."""
    write_changelog("## [9.1.0] - 2026-02-31\n")
    entries, issues = cur.parse_changelog()
    assert any("Invalid calendar date" in i for i in issues)
    assert entries[0].date_parsed is None


def test_parse_changelog_fallback_invalid_date_caught(
    write_changelog: WriteChangelog,
) -> None:
    """Fallback path encountering an invalid calendar date emits an issue."""
    write_changelog("## [9.1.0] - Released on 2026-02-31 (typo)\n")
    _entries, issues = cur.parse_changelog()
    assert any("Could not parse date from" in i for i in issues)


def test_parse_changelog_no_spaces_around_dash_flags_shape_issue(
    write_changelog: WriteChangelog,
) -> None:
    """``HEADER_RE`` allows ``-`` without surrounding whitespace, but the
    secondary shape regex on line 76 requires ``<space>-<space>``. A header
    written as ``## [9.1.0]-2026-05-19`` matches the first but not the
    second, surfacing as a ``Unexpected header shape`` issue.
    """
    write_changelog("## [9.1.0]-2026-05-19\n")
    _, issues = cur.parse_changelog()
    assert any("Unexpected header shape" in i for i in issues)


def test_parse_changelog_non_matching_lines_ignored(
    write_changelog: WriteChangelog,
) -> None:
    body = (
        "# Changelog\n"
        "Some intro text.\n"
        "## [9.1.0] - 2026-05-19\n"
        "### Added\n"
        "- Stuff\n"
        "## [9.0.0] - 2026-05-10\n"
    )
    write_changelog(body)
    entries, _ = cur.parse_changelog()
    versions = [e.version for e in entries]
    assert versions == ["9.1.0", "9.0.0"]


# --------------------------------------------------------- validate_changelog --
def test_validate_changelog_clean(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("## [9.1.0] - 2026-05-19\n## [9.0.0] - 2026-05-10\n")
    entries, _ = cur.parse_changelog()
    assert cur.validate_changelog(entries) == []


def test_validate_changelog_duplicates(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("## [9.1.0] - 2026-05-19\n## [9.0.0] - 2026-05-10\n## [9.1.0] - 2026-05-20\n")
    entries, _ = cur.parse_changelog()
    issues = cur.validate_changelog(entries)
    assert any("Duplicate version heading [9.1.0]" in i for i in issues)


def test_validate_changelog_ordering_violation(
    write_changelog: WriteChangelog,
) -> None:
    """A later entry with a NEWER date is a monotonicity violation."""
    write_changelog("## [9.0.0] - 2026-05-10\n## [9.1.0] - 2026-05-19\n")
    entries, _ = cur.parse_changelog()
    issues = cur.validate_changelog(entries)
    assert any("CHANGELOG ordering" in i for i in issues)


def test_validate_changelog_missing_dates_skipped_from_ordering(
    write_changelog: WriteChangelog,
) -> None:
    """Headers without parseable dates don't participate in ordering."""
    write_changelog("## [9.1.0] - no date here\n## [9.0.0] - 2026-05-10\n")
    entries, _ = cur.parse_changelog()
    issues = cur.validate_changelog(entries)
    assert not any("CHANGELOG ordering" in i for i in issues)


def test_validate_changelog_equal_dates_no_issue(
    write_changelog: WriteChangelog,
) -> None:
    """Monotonically non-INCREASING permits equal adjacent dates."""
    write_changelog("## [9.1.0] - 2026-05-19\n## [9.0.0] - 2026-05-19\n")
    entries, _ = cur.parse_changelog()
    issues = cur.validate_changelog(entries)
    assert issues == []


# ------------------------------------------------- collect_uc_definitions ----
def test_collect_uc_definitions_clean(fake_repo: pathlib.Path, write_uc: WriteUC) -> None:
    write_uc("cat-1-test", "1.1.1")
    write_uc("cat-2-test", "2.1.1")
    valid, issues = cur.collect_uc_definitions()
    assert valid == {"UC-1.1.1", "UC-2.1.1"}
    assert issues == []


def test_collect_uc_definitions_malformed_json_issue(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    write_uc("cat-1-test", "1.1.1", body="this { is not json")
    valid, issues = cur.collect_uc_definitions()
    assert valid == set()
    assert any("failed to parse" in i for i in issues)


def test_collect_uc_definitions_missing_id_skipped(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    write_uc("cat-1-test", "1.1.1", body={"no_id_field": True})
    valid, issues = cur.collect_uc_definitions()
    assert valid == set()
    assert issues == []


def test_collect_uc_definitions_non_canonical_id_skipped(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    write_uc("cat-1-test", "weird", body={"id": "not-a-real-id"})
    valid, issues = cur.collect_uc_definitions()
    assert valid == set()
    assert issues == []


def test_collect_uc_definitions_non_string_id_stringified(
    fake_repo: pathlib.Path, write_uc: WriteUC
) -> None:
    """``id`` as int gets stringified then regex-filtered."""
    write_uc("cat-1-test", "1.1.1", body={"id": 42})
    valid, _ = cur.collect_uc_definitions()
    assert valid == set()  # "42" fails the X.Y.Z pattern


def test_collect_uc_definitions_oserror_treated_as_failure(
    fake_repo: pathlib.Path,
    write_uc: WriteUC,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``OSError`` opening a sidecar surfaces as a parse-failure issue."""
    write_uc("cat-1-test", "1.1.1")

    real_open = pathlib.Path.open

    def boom_open(self: pathlib.Path, *a: Any, **kw: Any) -> Any:
        if self.name == "UC-1.1.1.json":
            raise OSError("permission denied")
        return real_open(self, *a, **kw)

    monkeypatch.setattr(pathlib.Path, "open", boom_open)
    valid, issues = cur.collect_uc_definitions()
    assert valid == set()
    assert any("failed to parse" in i for i in issues)


# ------------------------------------------------------ validate_uc_refs ----
def test_validate_uc_refs_missing_changelog_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    issues = cur.validate_uc_refs({"UC-1.1.1"})
    assert issues == []


def test_validate_uc_refs_clean(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("Released UC-1.1.1 and UC-2.1.1.\n")
    issues = cur.validate_uc_refs({"UC-1.1.1", "UC-2.1.1"})
    assert issues == []


def test_validate_uc_refs_unknown_uc_id(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("Removed UC-999.999.999 (legacy).\n")
    issues = cur.validate_uc_refs({"UC-1.1.1"})
    assert len(issues) == 1
    assert "UC-999.999.999" in issues[0]
    assert "CHANGELOG.md:1" in issues[0]


def test_validate_uc_refs_multiple_refs_per_line(
    write_changelog: WriteChangelog,
) -> None:
    write_changelog("Touched UC-1.1.1, UC-1.1.2, UC-2.2.2 in one go.\n")
    issues = cur.validate_uc_refs({"UC-1.1.1"})
    # UC-1.1.2 and UC-2.2.2 are broken
    broken = [i for i in issues if "UC-1.1.2" in i or "UC-2.2.2" in i]
    assert len(broken) == 2


def test_validate_uc_refs_long_snippet_truncated_at_240(
    write_changelog: WriteChangelog,
) -> None:
    line = "Released UC-1.1.1 with notes: " + ("x" * 300)
    write_changelog(line + "\n")
    issues = cur.validate_uc_refs(set())  # UC-1.1.1 not valid
    assert issues
    # The snippet is the third colon-separated chunk
    # format: "Broken UC cross-reference UC-1.1.1: CHANGELOG.md:1: <snippet>"
    # snippet length capped at 240
    suffix = issues[0].split(": ", 2)[2]
    assert len(suffix) <= 240


# ------------------------------------------------------------- main() -------
def test_main_clean_exits_zero(
    fake_repo: pathlib.Path,
    write_changelog: WriteChangelog,
    write_uc: WriteUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_uc("cat-1-test", "1.1.1")
    write_changelog("## [9.1.0] - 2026-05-19\n- Touched UC-1.1.1.\n## [9.0.0] - 2026-05-10\n")
    assert cur.main([]) == 0
    out = capsys.readouterr().out
    assert "Parsed 2 version headers" in out
    assert "Unique UC IDs from content/cat-*/UC-*.json: 1" in out
    assert "=== ALL ISSUES (0) ===" in out
    assert "None." in out


def test_main_with_issues_returns_one(
    fake_repo: pathlib.Path,
    write_changelog: WriteChangelog,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_changelog("## [9.1.0] - 2026-05-19\n- Broken UC-99.99.99.\n")
    assert cur.main([]) == 1
    out = capsys.readouterr().out
    assert "Broken UC cross-reference UC-99.99.99" in out


def test_main_truncates_after_five_entries(
    fake_repo: pathlib.Path,
    write_changelog: WriteChangelog,
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = "\n".join(f"## [{8 - i}.0.0] - 2026-05-{12 - i:02d}" for i in range(8))
    write_changelog(body + "\n")
    cur.main([])
    out = capsys.readouterr().out
    assert "Parsed 8 version headers" in out
    assert "... (3 more)" in out


def test_main_argv_none_falls_through(
    fake_repo: pathlib.Path,
    write_changelog: WriteChangelog,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_changelog("## [9.1.0] - 2026-05-19\n")
    monkeypatch.setattr(cur.sys, "argv", ["audit"])
    assert cur.main() == 0


def test_main_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cur.main(["--help"])
    assert exc.value.code == 0


# ---------------------------------------- dispatcher entry-point smoke -----
def test_module_dunder_main_exists() -> None:
    src = pathlib.Path(cur.__file__).read_text()
    assert 'if __name__ == "__main__":' in src
    assert "sys.exit(main())" in src
