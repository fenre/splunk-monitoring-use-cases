"""Tests for ``splunk_uc.audits.roadmap_consistency``.

P11 ROADMAP.md auditor. The audit is 656 lines covering ~20 small
helpers that parse and verify the public-facing roadmap document.
Before this file landed there were *zero* unit tests; coverage sat
at 0.0 %.

Strategy:

* Pure text parsers (``_split_sections``, ``_extract_release_entries``,
  ``_extract_next_up_version``, ``_next_up_heading``,
  ``_join_multiline_bullets``, ``_backlog_subsections``,
  ``_deprecated_items``, ``_versions_compatible``) are driven by
  carefully crafted Markdown fixtures.
* I/O helpers (``_git_head``, ``_read_version_triple``,
  ``_check_links``) get hermetic tests with ``tmp_path`` and
  ``monkeypatch`` against ``REPO_ROOT`` / ``VERSION_FILE`` /
  ``CHANGELOG_MD``.
* ``parse_roadmap`` and ``check_version_triple`` are exercised
  with synthetic roadmaps that wire every code path
  (structural errors, link rot, version drift).
* ``main`` is driven end-to-end with the roadmap relocated to
  ``tmp_path`` and ``--check`` / ``--strict-version`` / ``--export``
  modes asserted.

No real ``git`` invocation, no real ROADMAP.md, no network.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from splunk_uc.audits import roadmap_consistency as audit


# --------------------------------------------------------------------- #
# _git_head
# --------------------------------------------------------------------- #


def test_git_head_returns_empty_when_git_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*a: object, **k: object) -> object:
        raise FileNotFoundError("git: not found")

    monkeypatch.setattr(audit.subprocess, "run", _boom)
    assert audit._git_head() == ""


def test_git_head_returns_empty_when_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(*a: object, **k: object) -> object:
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=2)

    monkeypatch.setattr(audit.subprocess, "run", _boom)
    assert audit._git_head() == ""


def test_git_head_returns_empty_when_returncode_nonzero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Res:
        returncode = 128
        stdout = ""

    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _Res())
    assert audit._git_head() == ""


def test_git_head_returns_short_sha_when_git_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Res:
        returncode = 0
        stdout = "abc1234\n"

    monkeypatch.setattr(audit.subprocess, "run", lambda *a, **k: _Res())
    assert audit._git_head() == "abc1234"


# --------------------------------------------------------------------- #
# _read_version_triple
# --------------------------------------------------------------------- #


def test_read_version_triple_returns_none_pair_when_both_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "CHANGELOG.md")
    assert audit._read_version_triple() == (None, None)


def test_read_version_triple_reads_version_when_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "VERSION").write_text("9.2.0\n", encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "missing-CHANGELOG.md")
    version_text, changelog_top = audit._read_version_triple()
    assert version_text == "9.2.0"
    assert changelog_top is None


def test_read_version_triple_returns_none_for_empty_version_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "VERSION").write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "missing.md")
    version_text, _ = audit._read_version_triple()
    assert version_text is None


def test_read_version_triple_picks_first_released_changelog_entry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    body = (
        "# Changelog\n\n"
        "## [Unreleased]\n\n"
        "- WIP item\n\n"
        "## [9.2.0] - 2026-05-19\n\n"
        "- Things happened\n\n"
        "## [9.1.0] - 2026-04-12\n\n"
        "- More things happened\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(body, encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "missing-VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "CHANGELOG.md")
    _, changelog_top = audit._read_version_triple()
    assert changelog_top == "9.2.0"


def test_read_version_triple_returns_none_when_changelog_has_no_released_entry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    body = "# Changelog\n\n## [Unreleased]\n\n- nothing released yet\n"
    (tmp_path / "CHANGELOG.md").write_text(body, encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "missing-VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "CHANGELOG.md")
    _, changelog_top = audit._read_version_triple()
    assert changelog_top is None


# --------------------------------------------------------------------- #
# _split_sections
# --------------------------------------------------------------------- #


_MINIMAL_ROADMAP = """# Roadmap

## Current release

**v9.2 — Things** *(shipped 2026-05-19)*

## Previous releases

**v9.1 — More Things** *(shipped 2026-04-12)*

## Next up: v9.3 — Even more things

Plans …

## v10.0+ backlog (no fixed date)

### Content

- **Item A** — details

### Tooling

- **Item B** — details

## Deprecated / declined ideas

- **No SaaS** — historical commitment

## How to influence the roadmap

Open an issue or PR.
"""


def test_split_sections_finds_all_required_keys() -> None:
    sections = audit._split_sections(_MINIMAL_ROADMAP)
    for key, _ in audit._REQUIRED_SECTIONS:
        assert key in sections
        assert any(line.strip() for line in sections[key]), key


def test_split_sections_strips_horizontal_rule_markers() -> None:
    text = (
        "## Current release\n\n"
        "**v9.2 — X** *(shipped 2026-05-19)*\n"
        "\n---\n\n"
        "## Previous releases\n"
    )
    sections = audit._split_sections(text)
    assert "---" not in "\n".join(sections["current_release"])


def test_split_sections_captures_unknown_section_for_diagnostics() -> None:
    text = (
        "## Random unknown heading\n\n"
        "- not part of the roadmap shape\n\n"
        "## Current release\n\n"
        "**v9.2 — X** *(shipped 2026-05-19)*\n"
    )
    sections = audit._split_sections(text)
    assert any("Random unknown heading" in line for line in sections["__unknown__"])


def test_split_sections_ignores_lines_before_any_h2() -> None:
    """Lines that appear before the first ``## …`` heading must
    not land in any required section."""

    text = "preamble paragraph\n\nmore preamble\n\n## Current release\n\n**v9.2 — X** *(shipped 2026-05-19)*\n"
    sections = audit._split_sections(text)
    for key, _ in audit._REQUIRED_SECTIONS:
        assert "preamble" not in "\n".join(sections[key])


# --------------------------------------------------------------------- #
# _extract_release_entries
# --------------------------------------------------------------------- #


def test_extract_release_entries_parses_shipped_with_date() -> None:
    lines = ["**v9.2 — Quality Lift** *(shipped 2026-05-19)*"]
    entries = audit._extract_release_entries(lines)
    assert len(entries) == 1
    e = entries[0]
    assert e.version == "9.2"
    assert e.name == "Quality Lift"
    assert e.status == "shipped"
    assert e.date == "2026-05-19"


def test_extract_release_entries_parses_in_progress_without_date() -> None:
    lines = ["**v9.3 — Next Big Thing** *(in progress)*"]
    entries = audit._extract_release_entries(lines)
    assert len(entries) == 1
    e = entries[0]
    assert e.status == "in progress"
    assert e.date is None


def test_extract_release_entries_parses_cancelled() -> None:
    lines = ["**v9.0 — Scrapped** *(cancelled)*"]
    entries = audit._extract_release_entries(lines)
    assert entries[0].status == "cancelled"


def test_extract_release_entries_skips_non_matching_lines() -> None:
    lines = [
        "narrative paragraph about the release",
        "**v9.2 — X** *(shipped 2026-05-19)*",
        "- bullet that mentions v0.0 but isn't a release header",
    ]
    entries = audit._extract_release_entries(lines)
    assert [e.version for e in entries] == ["9.2"]


# --------------------------------------------------------------------- #
# _extract_next_up_version / _next_up_heading
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "heading, expected",
    [
        ("Next up: v9.3 — Even more things", "9.3"),
        ("Next up: v10.0.1 — Patch line", "10.0.1"),
        ("Next up: vNo.Version — junk", None),
    ],
)
def test_extract_next_up_version(heading: str, expected: str | None) -> None:
    assert audit._extract_next_up_version(heading) == expected


def test_next_up_heading_finds_first_match() -> None:
    text = "## Current release\n\n## Next up: v9.3 — Things\n"
    assert audit._next_up_heading(text) == "Next up: v9.3 — Things"


def test_next_up_heading_returns_none_when_absent() -> None:
    text = "## Current release\n\n## Previous releases\n"
    assert audit._next_up_heading(text) is None


# --------------------------------------------------------------------- #
# _join_multiline_bullets
# --------------------------------------------------------------------- #


def test_join_multiline_bullets_merges_continuation_lines() -> None:
    body = [
        "- **A** — first half",
        "  second half on a new line",
        "  third half on yet another line",
        "",
        "- **B** — single line",
    ]
    out = audit._join_multiline_bullets(body)
    assert out[0] == "- **A** — first half second half on a new line third half on yet another line"
    assert out[1] == ""
    assert out[2] == "- **B** — single line"


def test_join_multiline_bullets_resets_state_on_blank() -> None:
    """A blank line MUST reset the 'previous bullet' state so two
    adjacent paragraphs don't get mashed together."""

    body = [
        "- **A** — first",
        "",
        "  this would otherwise be appended to A",
    ]
    out = audit._join_multiline_bullets(body)
    # The "this would …" line is now its own non-bullet line, not a
    # continuation.
    assert "- **A** — first" == out[0]
    assert "" == out[1]
    assert "this would" in out[2]
    # And critically, ``A`` was not mutated.
    assert "this would" not in out[0]


def test_join_multiline_bullets_preserves_unrelated_text() -> None:
    body = ["paragraph", "- bullet", "more paragraph"]
    out = audit._join_multiline_bullets(body)
    assert out == ["paragraph", "- bullet", "more paragraph"]


# --------------------------------------------------------------------- #
# _backlog_subsections
# --------------------------------------------------------------------- #


def test_backlog_subsections_groups_by_h3() -> None:
    body = [
        "### Content",
        "- **Item A** — details",
        "- **Item B** — details",
        "",
        "### Tooling",
        "- **Item C** — details",
    ]
    out = audit._backlog_subsections(body)
    assert len(out) == 2
    assert out[0] == {"name": "Content", "items": ["**Item A** — details", "**Item B** — details"]}
    assert out[1] == {"name": "Tooling", "items": ["**Item C** — details"]}


def test_backlog_subsections_re_joins_multiline_bullets() -> None:
    body = [
        "### Content",
        "- **Industry-specific bundles** — Standalone content packs for",
        "  Finance, OT, Healthcare, …",
    ]
    out = audit._backlog_subsections(body)
    assert "Finance, OT, Healthcare" in out[0]["items"][0]


def test_backlog_subsections_ignores_lines_before_any_h3() -> None:
    body = [
        "narrative paragraph",
        "- bullet outside any H3",
        "### Content",
        "- **Item A**",
    ]
    out = audit._backlog_subsections(body)
    assert len(out) == 1
    assert out[0]["items"] == ["**Item A**"]


def test_backlog_subsections_returns_empty_on_empty_body() -> None:
    assert audit._backlog_subsections([]) == []


# --------------------------------------------------------------------- #
# _deprecated_items
# --------------------------------------------------------------------- #


def test_deprecated_items_extracts_top_level_bullets() -> None:
    body = [
        "- **No SaaS** — first commitment",
        "- **No commercial edition** — second commitment",
    ]
    out = audit._deprecated_items(body)
    assert out == [
        "**No SaaS** — first commitment",
        "**No commercial edition** — second commitment",
    ]


def test_deprecated_items_skips_non_bullet_lines() -> None:
    body = ["narrative", "- **Item A** — details", "more narrative"]
    out = audit._deprecated_items(body)
    assert out == ["**Item A** — details"]


def test_deprecated_items_returns_empty_when_no_bullets() -> None:
    assert audit._deprecated_items(["narrative only", ""]) == []


# --------------------------------------------------------------------- #
# _check_links
# --------------------------------------------------------------------- #


def test_check_links_passes_when_targets_exist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    (tmp_path / "CHANGELOG.md").write_text("# changelog\n", encoding="utf-8")
    text = "See [the changelog](CHANGELOG.md) for details."
    assert audit._check_links(text) == []


def test_check_links_flags_broken_repo_relative_links(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    text = "See [the missing doc](docs/does-not-exist.md)."
    issues = audit._check_links(text)
    assert len(issues) == 1
    assert "broken repo-relative link" in issues[0].message
    assert issues[0].severity == "error"


def test_check_links_skips_external_and_anchor_links(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    text = (
        "See [home](https://example.com), "
        "[mail](mailto:ops@example.com), "
        "[section](#other-section)."
    )
    assert audit._check_links(text) == []


def test_check_links_deduplicates_same_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    text = (
        "See [a](missing.md) and "
        "again [b](missing.md). Should report ONE broken-link issue, not two."
    )
    issues = audit._check_links(text)
    assert len(issues) == 1


def test_check_links_strips_anchor_fragment_from_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``docs/foo.md#some-anchor`` MUST resolve to ``docs/foo.md``."""

    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "foo.md").write_text("# Foo\n", encoding="utf-8")
    text = "See [foo](docs/foo.md#some-anchor) for details."
    assert audit._check_links(text) == []


def test_check_links_flags_target_that_escapes_repo_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    text = "See [escape](../../etc/passwd)."
    issues = audit._check_links(text)
    assert len(issues) == 1
    assert "escapes repo root" in issues[0].message
    assert issues[0].severity == "error"


def test_check_links_handles_empty_target() -> None:
    """``[link]()`` is malformed but mustn't crash the audit. The
    link regex doesn't match an empty ``href`` (it requires ``[^)\\s]+``),
    so the audit silently ignores it. This test pins that contract."""

    assert audit._check_links("see [link]()") == []


# --------------------------------------------------------------------- #
# _versions_compatible
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("v9.2", "9.2.0", True),
        ("9.2.0", "v9.2", True),
        ("v9.2", "9.3.0", False),
        ("v10.0", "v10.0.1", True),
        ("v10", "10.0.0", False),  # roadmap heading without minor is unusual
        ("garbage", "9.2.0", False),
        ("9.2.0", "more-garbage", False),
        # Bad triple still normalises to (-1,-1) on both sides → matches
        # itself (this is an intentional fallback).
        ("garbage", "morejunk", True),
    ],
)
def test_versions_compatible(a: str, b: str, expected: bool) -> None:
    assert audit._versions_compatible(a, b) is expected


# --------------------------------------------------------------------- #
# parse_roadmap
# --------------------------------------------------------------------- #


def test_parse_roadmap_populates_snapshot_and_no_issues_on_clean_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # _check_links walks REPO_ROOT — point it at an empty tmp_path so
    # any internal links in _MINIMAL_ROADMAP (there are none) won't
    # trip drift. We also make _git_head deterministic.
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(audit, "_git_head", lambda: "abc1234")

    snap, issues = audit.parse_roadmap(_MINIMAL_ROADMAP)

    assert snap.current_release == {
        "version": "9.2",
        "name": "Things",
        "status": "shipped",
        "date": "2026-05-19",
    }
    assert len(snap.previous_releases) == 1
    assert snap.previous_releases[0]["version"] == "9.1"
    assert snap.next_up == {"version": "9.3", "title": "Next up: v9.3 — Even more things"}
    assert len(snap.backlog) == 2
    assert snap.deprecated_ideas == ["**No SaaS** — historical commitment"]
    assert issues == []  # everything clean


def test_parse_roadmap_reports_missing_sections() -> None:
    """A roadmap that omits required sections must yield one
    error per missing section, plus collateral errors for the
    derived checks that depend on them."""

    text = "# Roadmap\n\n## Current release\n\n(empty)\n"
    snap, issues = audit.parse_roadmap(text)
    # Five of six required sections are missing.
    missing = [i for i in issues if "is missing or empty" in i.message]
    assert len(missing) == 5  # all except current_release, which has body lines

    # And the current_release body has no parseable release line,
    # so we should see that error too.
    assert any("does not declare a release" in i.message for i in issues)


def test_parse_roadmap_warns_when_previous_releases_empty() -> None:
    """An empty ``## Previous releases`` body is non-fatal but
    explicitly warning-tagged."""

    text = (
        "## Current release\n\n**v9.2 — X** *(shipped 2026-05-19)*\n\n"
        "## Previous releases\n\n_no prior releases yet_\n\n"
        "## Next up: v9.3 — Y\n\n"
        "## v10.0+ backlog (no fixed date)\n\n### Content\n\n- **A** — x\n\n"
        "## Deprecated / declined ideas\n\n- **No SaaS** — x\n\n"
        "## How to influence the roadmap\n\nfile an issue\n"
    )
    _, issues = audit.parse_roadmap(text)
    assert any(
        i.severity == "warning" and "Previous releases" in i.message for i in issues
    )


def test_parse_roadmap_warns_when_backlog_has_no_h3() -> None:
    text = (
        "## Current release\n\n**v9.2 — X** *(shipped 2026-05-19)*\n\n"
        "## Previous releases\n\n**v9.1 — A** *(shipped 2026-04-12)*\n\n"
        "## Next up: v9.3 — Y\n\n"
        "## v10.0+ backlog (no fixed date)\n\nbacklog narrative without H3 subsections\n\n"
        "## Deprecated / declined ideas\n\n- **No SaaS** — x\n\n"
        "## How to influence the roadmap\n\nfile an issue\n"
    )
    _, issues = audit.parse_roadmap(text)
    assert any(
        i.severity == "warning" and "backlog has no H3 subsections" in i.message
        for i in issues
    )


def test_parse_roadmap_errors_when_deprecated_is_empty() -> None:
    text = (
        "## Current release\n\n**v9.2 — X** *(shipped 2026-05-19)*\n\n"
        "## Previous releases\n\n**v9.1 — A** *(shipped 2026-04-12)*\n\n"
        "## Next up: v9.3 — Y\n\n"
        "## v10.0+ backlog (no fixed date)\n\n### Content\n\n- **A** — x\n\n"
        "## Deprecated / declined ideas\n\n(no bullets, just narrative)\n\n"
        "## How to influence the roadmap\n\nfile an issue\n"
    )
    _, issues = audit.parse_roadmap(text)
    assert any(
        i.severity == "error" and "Deprecated / declined ideas is empty" in i.message
        for i in issues
    )


def test_parse_roadmap_reports_broken_links(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    body = _MINIMAL_ROADMAP + "\nSee [missing](docs/does-not-exist.md).\n"
    _, issues = audit.parse_roadmap(body)
    assert any("broken repo-relative link" in i.message for i in issues)


# --------------------------------------------------------------------- #
# check_version_triple
# --------------------------------------------------------------------- #


def _hermetic_version_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    version: str | None,
    changelog: str | None,
) -> None:
    """Wire ``VERSION_FILE`` + ``CHANGELOG_MD`` to ``tmp_path``
    seeded with the given content."""

    if version is not None:
        (tmp_path / "VERSION").write_text(version, encoding="utf-8")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "VERSION")

    if changelog is not None:
        (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "CHANGELOG.md")


def test_check_version_triple_empty_when_everything_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    snap = audit._Snapshot(current_release={"version": "9.2"})
    assert audit.check_version_triple(snap, strict=False) == []


def test_check_version_triple_reports_missing_version_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version=None,
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    snap = audit._Snapshot(current_release={"version": "9.2"})
    issues = audit.check_version_triple(snap, strict=False)
    assert any("VERSION file missing" in i.message for i in issues)


def test_check_version_triple_reports_missing_changelog_entry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version="9.2.0",
        changelog="# Changelog\n\n## [Unreleased]\n",
    )
    snap = audit._Snapshot(current_release={"version": "9.2"})
    issues = audit.check_version_triple(snap, strict=False)
    assert any("no '## [X.Y.Z]" in i.message for i in issues)


def test_check_version_triple_warns_on_drift_in_non_strict_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    snap = audit._Snapshot(current_release={"version": "7.1"})  # stale roadmap
    issues = audit.check_version_triple(snap, strict=False)
    drift = [i for i in issues if "Current release" in i.message]
    assert drift
    assert all(i.severity == "warning" for i in drift)


def test_check_version_triple_errors_on_drift_in_strict_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    snap = audit._Snapshot(current_release={"version": "7.1"})
    issues = audit.check_version_triple(snap, strict=True)
    drift = [i for i in issues if "Current release" in i.message]
    assert drift
    assert all(i.severity == "error" for i in drift)


def test_check_version_triple_reports_changelog_drift_separately(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When roadmap and VERSION agree but the changelog top entry
    is for a different release, we get a separate drift issue."""

    _hermetic_version_files(
        monkeypatch,
        tmp_path,
        version="9.2.0",
        changelog="## [8.0.0] - 2025-12-01\n",
    )
    snap = audit._Snapshot(current_release={"version": "9.2"})
    issues = audit.check_version_triple(snap, strict=False)
    assert any(
        "top CHANGELOG.md entry is 8.0.0" in i.message and i.severity == "warning"
        for i in issues
    )


# --------------------------------------------------------------------- #
# _Issue / _snapshot_to_dict
# --------------------------------------------------------------------- #


def test_issue_format_emits_correct_prefix() -> None:
    e = audit._Issue("error", "boom")
    w = audit._Issue("warning", "tut")
    assert e.format() == "ERROR: boom"
    assert w.format() == "WARN : tut"


def test_snapshot_to_dict_serialises_every_field() -> None:
    snap = audit._Snapshot(
        schema_version="1.0",
        captured_at="2026-05-20T00:00:00Z",
        git_head="abc1234",
        current_release={"version": "9.2"},
        previous_releases=[{"version": "9.1"}],
        next_up={"version": "9.3"},
        backlog=[{"name": "Content", "items": ["x"]}],
        deprecated_ideas=["**No SaaS**"],
    )
    payload = audit._snapshot_to_dict(snap)
    assert payload["schema_version"] == "1.0"
    assert payload["current_release"] == {"version": "9.2"}
    assert payload["previous_releases"] == [{"version": "9.1"}]
    assert payload["next_up"] == {"version": "9.3"}
    assert payload["backlog"] == [{"name": "Content", "items": ["x"]}]
    assert payload["deprecated_ideas"] == ["**No SaaS**"]
    # Round-trip through JSON to confirm serialisability.
    assert json.loads(json.dumps(payload)) == payload


# --------------------------------------------------------------------- #
# _build_argparser
# --------------------------------------------------------------------- #


def test_build_argparser_defaults() -> None:
    parser = audit._build_argparser()
    ns = parser.parse_args([])
    assert ns.check is False
    assert ns.strict_version is False
    assert ns.export is None


def test_build_argparser_accepts_all_flags() -> None:
    parser = audit._build_argparser()
    ns = parser.parse_args(["--check", "--strict-version", "--export", "out.json"])
    assert ns.check is True
    assert ns.strict_version is True
    assert ns.export == Path("out.json")


# --------------------------------------------------------------------- #
# main — end-to-end
# --------------------------------------------------------------------- #


def _hermetic_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    roadmap: str,
    version: str,
    changelog: str,
) -> None:
    """Wire ROADMAP.md / VERSION / CHANGELOG.md / REPO_ROOT into
    ``tmp_path`` with the given content."""

    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "VERSION").write_text(version, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    monkeypatch.setattr(audit, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(audit, "ROADMAP_MD", tmp_path / "ROADMAP.md")
    monkeypatch.setattr(audit, "VERSION_FILE", tmp_path / "VERSION")
    monkeypatch.setattr(audit, "CHANGELOG_MD", tmp_path / "CHANGELOG.md")
    monkeypatch.setattr(audit, "_git_head", lambda: "abc1234")


def test_main_returns_two_when_roadmap_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(audit, "ROADMAP_MD", tmp_path / "no-such-roadmap.md")
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 2
    assert "ROADMAP.md missing" in err


def test_main_returns_zero_on_clean_input_with_version_drift_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default --check mode: structural errors fail, version drift only warns."""

    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=_MINIMAL_ROADMAP,  # advertises v9.2
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    rc = audit.main([])
    assert rc == 0
    err = capsys.readouterr().err
    assert err == ""  # zero issues at all


def test_main_returns_zero_when_only_warnings_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Version drift in non-strict mode prints a WARN but does
    not fail the build."""

    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=_MINIMAL_ROADMAP,  # advertises v9.2
        version="9.5.0",  # drifted
        changelog="## [9.5.0] - 2026-06-19\n",
    )
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 0
    assert "WARN" in err
    assert "Current release" in err


def test_main_returns_one_in_strict_mode_on_version_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=_MINIMAL_ROADMAP,
        version="9.5.0",
        changelog="## [9.5.0] - 2026-06-19\n",
    )
    rc = audit.main(["--strict-version"])
    err = capsys.readouterr().err
    assert rc == 1
    assert "ERROR" in err


def test_main_returns_one_on_structural_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ROADMAP.md missing required sections fails even in
    non-strict mode."""

    text = "## Current release\n\n**v9.2 — X** *(shipped 2026-05-19)*\n"
    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=text,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    rc = audit.main([])
    err = capsys.readouterr().err
    assert rc == 1
    assert "ERROR" in err


def test_main_export_writes_json_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=_MINIMAL_ROADMAP,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    export = tmp_path / "snapshots" / "roadmap.json"
    rc = audit.main(["--export", str(export)])
    err = capsys.readouterr().err
    assert rc == 0
    assert f"wrote roadmap snapshot to {export}" in err
    assert export.is_file()
    payload = json.loads(export.read_text(encoding="utf-8"))
    assert payload["schema_version"] == audit.SCHEMA_VERSION
    assert payload["current_release"]["version"] == "9.2"


def test_main_export_resolves_relative_paths_against_repo_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _hermetic_main(
        monkeypatch,
        tmp_path,
        roadmap=_MINIMAL_ROADMAP,
        version="9.2.0",
        changelog="## [9.2.0] - 2026-05-19\n",
    )
    rc = audit.main(["--export", "out/roadmap.json"])
    assert rc == 0
    assert (tmp_path / "out" / "roadmap.json").is_file()
