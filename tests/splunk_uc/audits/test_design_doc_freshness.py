"""Unit tests pinning ``splunk_uc.audits.design_doc_freshness``.

The audit walks ``docs/DESIGN.md`` and surfaces two classes of freshness
drift:

1. **Section drift.** The H2 headings in DESIGN.md must match the canonical
   list (``CANONICAL_SECTIONS``); anything missing surfaces as
   ``missing-section`` and anything unexpected surfaces as
   ``extra-section`` (the literal "Table of contents" is whitelisted).

2. **Broken links.** Every markdown link target that is not an external
   URL (``http://``, ``https://``, ``mailto:``) and not an in-page anchor
   (``#section``) must resolve to an existing file relative to
   ``docs/``.

The audit is **non-gating by default** — it warns and exits 0 even when
issues are found. The ``--strict`` flag flips the exit code to 1 so CI
can opt into hard-fail mode.

These tests are hermetic — each one builds a synthetic ``docs/`` tree
under ``tmp_path`` and monkey-patches ``ddf.DESIGN_MD`` (the module-level
absolute path constant) so the audit reads our fixture instead of the
live DESIGN.md.
"""

from __future__ import annotations

import pathlib
from typing import Protocol

import pytest

from splunk_uc.audits import design_doc_freshness as ddf


class WriteDesign(Protocol):
    """Factory protocol for writing a synthetic ``DESIGN.md``."""

    def __call__(self, body: str) -> pathlib.Path: ...


@pytest.fixture
def fake_docs(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a fake ``docs/`` tree and rewire ``ddf.DESIGN_MD``.

    Returns the ``docs/`` directory path so individual tests can drop
    target files alongside the synthetic ``DESIGN.md`` for the
    broken-link matrix.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    design_path = docs_dir / "DESIGN.md"
    monkeypatch.setattr(ddf, "DESIGN_MD", str(design_path))
    return docs_dir


@pytest.fixture
def write_design(fake_docs: pathlib.Path) -> WriteDesign:
    """Return a factory that writes ``docs/DESIGN.md`` and returns its path."""

    def _make(body: str) -> pathlib.Path:
        path = fake_docs / "DESIGN.md"
        path.write_text(body, encoding="utf-8")
        return path

    return _make


def _all_sections_md() -> str:
    """Return DESIGN.md body with all 17 canonical H2 sections."""
    return "\n".join(f"## {section}\n\nbody\n" for section in ddf.CANONICAL_SECTIONS)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_script_dir_resolves_to_audits_directory() -> None:
    """SCRIPT_DIR points at the audits/ package directory."""
    assert pathlib.Path(ddf.SCRIPT_DIR).name == "audits"
    assert pathlib.Path(ddf.SCRIPT_DIR).is_absolute()


def test_repo_root_resolves_to_three_parents_up() -> None:
    """REPO_ROOT walks three parents up to land at the repo root.

    The docstring explicitly calls out the legacy ``parent.parent`` chain
    that was wrong by three; pin the corrected behaviour.
    """
    repo_root = pathlib.Path(ddf.REPO_ROOT)
    assert repo_root.is_absolute()
    assert (repo_root / "src" / "splunk_uc" / "audits").is_dir()


def test_design_md_lives_under_docs() -> None:
    """DESIGN_MD is the repo-relative ``docs/DESIGN.md`` path."""
    design_path = pathlib.Path(ddf.DESIGN_MD)
    assert design_path.name == "DESIGN.md"
    assert design_path.parent.name == "docs"


def test_canonical_sections_has_seventeen_entries() -> None:
    """The canonical list has exactly 17 entries, ordered 1..17."""
    assert len(ddf.CANONICAL_SECTIONS) == 17
    for i, heading in enumerate(ddf.CANONICAL_SECTIONS, start=1):
        assert heading.startswith(f"{i}. "), heading


def test_canonical_sections_have_unique_entries() -> None:
    """No duplicates in the canonical section list."""
    assert len(ddf.CANONICAL_SECTIONS) == len(set(ddf.CANONICAL_SECTIONS))


def test_link_re_matches_markdown_inline_link() -> None:
    """``LINK_RE`` extracts the parenthesised target from a markdown link."""
    assert ddf.LINK_RE.findall("[text](target.md)") == ["target.md"]
    assert ddf.LINK_RE.findall("foo [a](b) bar [c](d)") == ["b", "d"]


def test_link_re_does_not_match_reference_style_links() -> None:
    """Reference-style links (``[text][ref]``) are NOT matched.

    The audit only inspects inline ``[text](url)`` form. This pins that
    contract so reference-style refactors don't silently change the
    scope of the audit.
    """
    assert ddf.LINK_RE.findall("[text][ref]") == []


def test_link_re_does_not_match_image_targets() -> None:
    """Image syntax ``![alt](src)`` is matched verbatim — alt is square-bracketed.

    The regex ``\\[[^\\]]+\\]\\(([^)]+)\\)`` requires at least one char
    inside the square brackets, but image links have the same shape with
    a leading ``!`` — the regex captures the URL part regardless of the
    leading exclamation mark. Pin this so future refactors don't silently
    skip images.
    """
    assert ddf.LINK_RE.findall("![alt](image.png)") == ["image.png"]


# ---------------------------------------------------------------------------
# read_design
# ---------------------------------------------------------------------------


def test_read_design_returns_file_contents(write_design: WriteDesign) -> None:
    """A present DESIGN.md is read into a UTF-8 string."""
    write_design("hello\n")
    assert ddf.read_design() == "hello\n"


def test_read_design_exits_2_when_missing(
    fake_docs: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing DESIGN.md exits with code 2 and writes to stderr."""
    with pytest.raises(SystemExit) as exc:
        ddf.read_design()
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "FAIL:" in captured.err
    assert "not found" in captured.err


def test_read_design_uses_utf8_encoding(write_design: WriteDesign) -> None:
    """Non-ASCII content round-trips cleanly (UTF-8 decoding)."""
    body = "## 1. Purpose and scope\n\néàñ unicode 🚀\n"
    write_design(body)
    assert ddf.read_design() == body


# ---------------------------------------------------------------------------
# extract_h2_sections
# ---------------------------------------------------------------------------


def test_extract_h2_sections_pulls_out_h2_headings() -> None:
    """``## `` headings are extracted; their text-after-prefix is captured."""
    body = "## First\n## Second\n\nbody\n## Third\n"
    assert ddf.extract_h2_sections(body) == ["First", "Second", "Third"]


def test_extract_h2_sections_ignores_h1_and_h3() -> None:
    """Only level-2 headings are captured; H1 and H3 are skipped."""
    body = "# H1 heading\n### H3 heading\n## H2 heading\n"
    assert ddf.extract_h2_sections(body) == ["H2 heading"]


def test_extract_h2_sections_strips_trailing_whitespace() -> None:
    """Trailing whitespace and tabs are stripped from the captured text."""
    body = "## Heading with trailing space   \n## Tab heading\t\n"
    assert ddf.extract_h2_sections(body) == [
        "Heading with trailing space",
        "Tab heading",
    ]


def test_extract_h2_sections_handles_empty_input() -> None:
    """Empty body returns empty list."""
    assert ddf.extract_h2_sections("") == []


def test_extract_h2_sections_ignores_indented_h2() -> None:
    """Indented ``## `` does NOT match (regex anchors on ``^##``)."""
    body = "    ## Indented heading\n## Real heading\n"
    assert ddf.extract_h2_sections(body) == ["Real heading"]


def test_extract_h2_sections_requires_space_after_hashes() -> None:
    """``##NoSpace`` does NOT match — the regex requires ``##\\s+``."""
    body = "##NoSpace heading\n## Valid heading\n"
    assert ddf.extract_h2_sections(body) == ["Valid heading"]


def test_extract_h2_sections_does_not_match_hash_inside_text() -> None:
    """A literal ``## `` in mid-line text is NOT captured (line-start anchored)."""
    body = "Some text ## not a heading\n## Real heading\n"
    assert ddf.extract_h2_sections(body) == ["Real heading"]


# ---------------------------------------------------------------------------
# resolve_link
# ---------------------------------------------------------------------------


def test_resolve_link_skips_http_url() -> None:
    """``http://...`` targets are considered OK with marker ``skip``."""
    ok, marker = ddf.resolve_link("http://example.com/foo", "/tmp/docs")
    assert ok is True
    assert marker == "skip"


def test_resolve_link_skips_https_url() -> None:
    """``https://...`` targets are considered OK."""
    ok, marker = ddf.resolve_link("https://example.com/foo", "/tmp/docs")
    assert ok is True
    assert marker == "skip"


def test_resolve_link_skips_mailto() -> None:
    """``mailto:...`` targets are considered OK."""
    ok, marker = ddf.resolve_link("mailto:foo@example.com", "/tmp/docs")
    assert ok is True
    assert marker == "skip"


def test_resolve_link_skips_in_page_anchor() -> None:
    """A bare ``#anchor`` target is considered OK (in-page TOC link)."""
    ok, marker = ddf.resolve_link("#section-name", "/tmp/docs")
    assert ok is True
    assert marker == "skip"


def test_resolve_link_returns_ok_for_existing_relative_target(
    fake_docs: pathlib.Path,
) -> None:
    """A relative target that exists on disk returns ``True``."""
    (fake_docs / "sibling.md").write_text("sibling", encoding="utf-8")
    ok, resolved = ddf.resolve_link("sibling.md", str(fake_docs))
    assert ok is True
    assert resolved.endswith("/sibling.md")


def test_resolve_link_returns_false_for_missing_relative_target(
    fake_docs: pathlib.Path,
) -> None:
    """A relative target that does NOT exist returns ``False``."""
    ok, resolved = ddf.resolve_link("missing.md", str(fake_docs))
    assert ok is False
    assert resolved.endswith("/missing.md")


def test_resolve_link_handles_parent_directory_traversal(
    fake_docs: pathlib.Path,
) -> None:
    """``../`` traversal resolves correctly against ``doc_dir``."""
    repo_root = fake_docs.parent
    (repo_root / "README.md").write_text("readme", encoding="utf-8")
    ok, resolved = ddf.resolve_link("../README.md", str(fake_docs))
    assert ok is True
    assert resolved.endswith("/README.md")


def test_resolve_link_strips_fragment_before_check(
    fake_docs: pathlib.Path,
) -> None:
    """A ``file.md#anchor`` link checks ``file.md`` (anchor stripped)."""
    (fake_docs / "file.md").write_text("body", encoding="utf-8")
    ok, resolved = ddf.resolve_link("file.md#anchor", str(fake_docs))
    assert ok is True
    assert resolved.endswith("/file.md")


def test_resolve_link_empty_string_after_anchor_strip_is_ok(
    fake_docs: pathlib.Path,
) -> None:
    """A target that becomes empty after fragment-strip is treated as OK.

    Edge case: a target like ``#`` would strip to ``""`` and the
    audit returns ``(True, "skip")`` rather than trying to check
    the empty path. But ``#`` is also caught by the in-page anchor
    branch above. Test the more direct ``""``-after-strip via
    ``""`` directly.
    """
    ok, marker = ddf.resolve_link("", str(fake_docs))
    assert ok is True
    assert marker == "skip"


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_returns_0_when_all_sections_present(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """All 17 canonical sections present → exit 0 with success message."""
    write_design(_all_sections_md())
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "OK: DESIGN.md has all 17 canonical sections" in captured.out
    assert "all relative links resolve" in captured.out


def test_main_strict_returns_0_when_clean(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--strict`` doesn't change exit code when there are no issues."""
    write_design(_all_sections_md())
    assert ddf.main(["--strict"]) == 0
    captured = capsys.readouterr()
    assert "OK:" in captured.out


def test_main_argv_none_uses_sys_argv_default(
    write_design: WriteDesign,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``argv=None`` falls through to argparse's ``sys.argv`` default."""
    monkeypatch.setattr("sys.argv", ["audit-design-doc-freshness"])
    write_design(_all_sections_md())
    assert ddf.main(None) == 0


def test_main_help_exits_clean(capsys: pytest.CaptureFixture[str]) -> None:
    """``--help`` exits with code 0 and prints argparse help text."""
    with pytest.raises(SystemExit) as exc:
        ddf.main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--strict" in captured.out


def test_main_allows_table_of_contents_extra_heading(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """The literal "Table of contents" heading does NOT count as extra."""
    body = "## Table of contents\n\n" + _all_sections_md()
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "extra-section" not in captured.out


# ---------------------------------------------------------------------------
# main() — missing-section detection
# ---------------------------------------------------------------------------


def test_main_flags_missing_canonical_section(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing canonical section surfaces as ``missing-section`` warning."""
    # Drop the last section.
    body = "\n".join(f"## {section}\n" for section in ddf.CANONICAL_SECTIONS[:-1])
    write_design(body)
    assert ddf.main([]) == 0  # non-gating without --strict
    captured = capsys.readouterr()
    assert "DESIGN.md freshness issues:" in captured.out
    assert "missing-section:" in captured.out
    assert ddf.CANONICAL_SECTIONS[-1] in captured.out


def test_main_flags_all_missing_when_empty_doc(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty DESIGN.md surfaces all 17 sections as missing."""
    write_design("")
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out.count("missing-section:") == 17


def test_main_strict_returns_1_when_section_missing(
    write_design: WriteDesign,
) -> None:
    """``--strict`` flips exit code to 1 when issues exist."""
    write_design("## 1. Purpose and scope\n")
    assert ddf.main(["--strict"]) == 1


# ---------------------------------------------------------------------------
# main() — extra-section detection
# ---------------------------------------------------------------------------


def test_main_flags_extra_non_canonical_section(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """A non-canonical H2 surfaces as ``extra-section`` warning."""
    body = _all_sections_md() + "\n## Unexpected heading\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "extra-section: 'Unexpected heading'" in captured.out


def test_main_does_not_flag_table_of_contents_as_extra(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """``Table of contents`` is the documented exception to extra-section."""
    body = "## Table of contents\n" + _all_sections_md()
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "extra-section" not in captured.out
    assert "OK:" in captured.out


# ---------------------------------------------------------------------------
# main() — broken-link detection
# ---------------------------------------------------------------------------


def test_main_flags_broken_relative_link(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """A relative link to a missing file surfaces as ``broken-link``."""
    body = _all_sections_md() + "\n\n[Broken](missing-doc.md)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link: 'missing-doc.md'" in captured.out


def test_main_does_not_flag_existing_relative_link(
    write_design: WriteDesign,
    fake_docs: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An existing relative link doesn't surface as a warning."""
    (fake_docs / "sibling.md").write_text("body", encoding="utf-8")
    body = _all_sections_md() + "\n\n[Sibling](sibling.md)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link" not in captured.out
    assert "OK:" in captured.out


def test_main_does_not_flag_external_url_link(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """External ``https://`` links are not checked."""
    body = _all_sections_md() + "\n\n[External](https://example.com/x)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link" not in captured.out


def test_main_does_not_flag_in_page_anchor(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """In-page anchors ``[Top](#top)`` are not checked."""
    body = _all_sections_md() + "\n\n[Top](#top)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link" not in captured.out


def test_main_strict_returns_1_when_link_broken(
    write_design: WriteDesign,
) -> None:
    """``--strict`` flips exit to 1 when only a broken link is present."""
    body = _all_sections_md() + "\n\n[Broken](nowhere.md)\n"
    write_design(body)
    assert ddf.main(["--strict"]) == 1


def test_main_multiple_broken_links_all_reported(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every broken link surfaces as its own warning line."""
    body = _all_sections_md() + "\n\n[A](a.md)\n[B](b.md)\n[C](c.md)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link: 'a.md'" in captured.out
    assert "broken-link: 'b.md'" in captured.out
    assert "broken-link: 'c.md'" in captured.out


def test_main_link_with_fragment_strips_anchor_before_check(
    write_design: WriteDesign,
    fake_docs: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``file.md#anchor`` link checks ``file.md`` (anchor stripped)."""
    (fake_docs / "exists.md").write_text("body", encoding="utf-8")
    body = _all_sections_md() + "\n\n[Anchored](exists.md#section)\n"
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "broken-link" not in captured.out


# ---------------------------------------------------------------------------
# main() — combined issue surfacing
# ---------------------------------------------------------------------------


def test_main_reports_section_and_link_issues_in_same_run(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """Multiple kinds of issues all surface in the same run."""
    body = (
        "## 1. Purpose and scope\n"  # only one canonical section
        "## Unexpected\n"
        "\n[Broken](nowhere.md)\n"
    )
    write_design(body)
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "missing-section:" in captured.out
    assert "extra-section: 'Unexpected'" in captured.out
    assert "broken-link: 'nowhere.md'" in captured.out


def test_main_non_strict_message_includes_strict_hint(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """Non-strict mode prints the ``--strict`` hint after the issues block."""
    write_design("## Unexpected\n")
    assert ddf.main([]) == 0
    captured = capsys.readouterr()
    assert "(non-gating; pass --strict to fail)" in captured.out


def test_main_strict_mode_does_not_print_strict_hint(
    write_design: WriteDesign, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--strict`` mode does NOT print the ``pass --strict`` hint."""
    write_design("## Unexpected\n")
    assert ddf.main(["--strict"]) == 1
    captured = capsys.readouterr()
    assert "(non-gating; pass --strict to fail)" not in captured.out


# ---------------------------------------------------------------------------
# main() — missing DESIGN.md propagation
# ---------------------------------------------------------------------------


def test_main_propagates_exit_2_from_read_design(
    fake_docs: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing DESIGN.md exits 2 via ``read_design()`` ``sys.exit``."""
    # Don't create DESIGN.md → read_design() raises SystemExit(2).
    with pytest.raises(SystemExit) as exc:
        ddf.main([])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "FAIL:" in captured.err


# ---------------------------------------------------------------------------
# Script entry-point smoke
# ---------------------------------------------------------------------------


def test_main_with_argv_strict_explicit_false(
    write_design: WriteDesign,
) -> None:
    """Explicitly passing no ``--strict`` is the same as default."""
    write_design(_all_sections_md())
    assert ddf.main([]) == 0
