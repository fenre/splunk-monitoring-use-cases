"""Comprehensive unit tests for ``src/splunk_uc/audits/doc_counts.py``.

Pins every documented contract of the doc-freshness audit:

- module constants (``PROJECT_ROOT`` resolved, ``CHECKS`` exactly the three
  documented entries with the documented regex and check_type);
- ``get_actual_uc_count`` (counts ``UC-*.json`` under ``content/`` recursively);
- ``get_actual_category_count`` (counts ``cat-*`` directories under ``content/``);
- ``main()`` exit-code matrix (drift > 5% → exit 1, within tolerance → exit 0,
  missing doc files skipped silently);
- regex matching across the three doc patterns ("use cases" / "use-cases" /
  "UCs"), thousands-separator comma handling in claimed values, and the
  ``+`` suffix being tolerated.
"""

from __future__ import annotations

import pathlib
from typing import Protocol

import pytest

from splunk_uc.audits import doc_counts as dc


class WriteContent(Protocol):
    def __call__(self, count: int) -> None: ...


class WriteDoc(Protocol):
    def __call__(self, rel: str, body: str) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build a hermetic content/ + docs/ skeleton and patch PROJECT_ROOT."""
    (tmp_path / "content").mkdir()
    (tmp_path / "docs").mkdir()
    monkeypatch.setattr(dc, "PROJECT_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def write_content(fake_repo: pathlib.Path) -> WriteContent:
    """Factory that materialises N UC sidecars across categories."""

    def _make(count: int) -> None:
        cat = fake_repo / "content" / "cat-01-foo"
        cat.mkdir(exist_ok=True)
        for i in range(count):
            (cat / f"UC-1.1.{i + 1}.json").write_text("{}", encoding="utf-8")

    return _make


@pytest.fixture
def write_doc(fake_repo: pathlib.Path) -> WriteDoc:
    """Factory that materialises a doc file with arbitrary body."""

    def _make(rel: str, body: str) -> pathlib.Path:
        p = fake_repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        return p

    return _make


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------


def test_project_root_resolves_to_absolute_path() -> None:
    """`PROJECT_ROOT` is a resolved absolute path at import time."""
    assert isinstance(dc.PROJECT_ROOT, pathlib.Path)
    assert dc.PROJECT_ROOT.is_absolute()


def test_checks_is_three_documented_entries() -> None:
    """`CHECKS` is exactly the three documented doc-file tuples."""
    assert len(dc.CHECKS) == 3
    rel_paths = [c[0] for c in dc.CHECKS]
    assert rel_paths == ["AGENTS.md", "docs/PITCH.md", "docs/architecture.md"]
    for _, _, check_type in dc.CHECKS:
        assert check_type == "uc_count"


def test_checks_pattern_matches_use_cases_variants() -> None:
    """The CHECKS regex matches all three documented phrase variants."""
    import re

    pat = dc.CHECKS[0][1]
    matches_uc = re.findall(pat, "5000+ use cases", re.IGNORECASE)
    matches_dash = re.findall(pat, "5000+ use-cases", re.IGNORECASE)
    matches_ucs = re.findall(pat, "5000+ UCs", re.IGNORECASE)
    assert matches_uc == ["5000"]
    assert matches_dash == ["5000"]
    assert matches_ucs == ["5000"]


def test_checks_pattern_captures_thousands_separator() -> None:
    """Pattern `\\d[\\d,]+` accepts comma-separated thousands."""
    import re

    pat = dc.CHECKS[0][1]
    matches = re.findall(pat, "7,929 use cases", re.IGNORECASE)
    assert matches == ["7,929"]


# ---------------------------------------------------------------------------
# get_actual_uc_count
# ---------------------------------------------------------------------------


def test_get_actual_uc_count_empty(fake_repo: pathlib.Path) -> None:
    """Empty content tree returns 0."""
    assert dc.get_actual_uc_count() == 0


def test_get_actual_uc_count_recursive(
    fake_repo: pathlib.Path, write_content: WriteContent
) -> None:
    """`rglob('UC-*.json')` recursively counts all UC sidecars."""
    write_content(7)
    assert dc.get_actual_uc_count() == 7


def test_get_actual_uc_count_across_categories(
    fake_repo: pathlib.Path,
) -> None:
    """UCs spread across multiple cat-NN-foo directories are all counted."""
    cat1 = fake_repo / "content" / "cat-01-foo"
    cat2 = fake_repo / "content" / "cat-02-bar"
    cat1.mkdir()
    cat2.mkdir()
    (cat1 / "UC-1.1.1.json").write_text("{}", encoding="utf-8")
    (cat1 / "UC-1.1.2.json").write_text("{}", encoding="utf-8")
    (cat2 / "UC-2.1.1.json").write_text("{}", encoding="utf-8")
    assert dc.get_actual_uc_count() == 3


def test_get_actual_uc_count_ignores_non_uc_files(
    fake_repo: pathlib.Path,
) -> None:
    """Files not matching `UC-*.json` are NOT counted."""
    cat = fake_repo / "content" / "cat-01-foo"
    cat.mkdir()
    (cat / "UC-1.1.1.json").write_text("{}", encoding="utf-8")
    (cat / "README.md").write_text("noise", encoding="utf-8")
    (cat / "notes.json").write_text("{}", encoding="utf-8")
    assert dc.get_actual_uc_count() == 1


# ---------------------------------------------------------------------------
# get_actual_category_count
# ---------------------------------------------------------------------------


def test_get_actual_category_count_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Empty content tree returns 0."""
    assert dc.get_actual_category_count() == 0


def test_get_actual_category_count_multiple(
    fake_repo: pathlib.Path,
) -> None:
    """Each `cat-*` directory adds to the count."""
    for i in range(3):
        (fake_repo / "content" / f"cat-0{i + 1}-foo").mkdir()
    assert dc.get_actual_category_count() == 3


def test_get_actual_category_count_ignores_non_cat_dirs(
    fake_repo: pathlib.Path,
) -> None:
    """Non-`cat-*` directories are NOT counted."""
    (fake_repo / "content" / "cat-01-foo").mkdir()
    (fake_repo / "content" / "schemas").mkdir()
    (fake_repo / "content" / "templates").mkdir()
    assert dc.get_actual_category_count() == 1


def test_get_actual_category_count_counts_dirs_and_files_alike(
    fake_repo: pathlib.Path,
) -> None:
    """`glob` matches both files and dirs — if a `cat-foo` file exists, it counts.

    This is a quirk of the source `glob("cat-*")` call (no `is_dir()` filter),
    pinned here as documented behaviour.
    """
    (fake_repo / "content" / "cat-01-foo").mkdir()
    (fake_repo / "content" / "cat-stray.md").write_text("noise", encoding="utf-8")
    assert dc.get_actual_category_count() == 2


# ---------------------------------------------------------------------------
# main() — empty content edge case
# ---------------------------------------------------------------------------


def test_main_zero_actual_with_no_docs_returns_zero(
    fake_repo: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """0 UCs + no docs to check → exit 0 with all-clean message."""
    assert dc.main([]) == 0
    out = capsys.readouterr().out
    assert "Doc freshness:" in out
    assert "(0 UCs)" in out


def test_main_argv_is_ignored(
    fake_repo: pathlib.Path,
) -> None:
    """`del argv` means any value is accepted."""
    assert dc.main(["--unknown", "foo"]) == 0


def test_main_argv_none_accepted(
    fake_repo: pathlib.Path,
) -> None:
    """`argv=None` is also accepted."""
    assert dc.main(None) == 0


# ---------------------------------------------------------------------------
# main() — happy paths
# ---------------------------------------------------------------------------


def test_main_exact_match_passes(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A doc with the exact actual count → exit 0 + success message."""
    write_content(100)
    write_doc("AGENTS.md", "We have 100+ use cases.")
    assert dc.main([]) == 0
    out = capsys.readouterr().out
    assert "all checked counts within 5% of actual" in out
    assert "100 UCs" in out


def test_main_within_tolerance_passes(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Claimed value within 5% of actual passes (4% drift OK)."""
    write_content(100)
    write_doc("AGENTS.md", "We have 104+ use cases.")
    assert dc.main([]) == 0


def test_main_exact_5_percent_drift_passes(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Exactly 5% drift is NOT flagged (strict greater-than)."""
    write_content(100)
    write_doc("AGENTS.md", "We have 105 use cases.")
    assert dc.main([]) == 0


def test_main_thousands_separator_handled(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Claimed value like `7,929` is parsed as integer 7929."""
    write_content(7929)
    write_doc("AGENTS.md", "We have 7,929 use cases.")
    assert dc.main([]) == 0


def test_main_three_docs_all_match(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """All three documented docs are inspected."""
    write_content(100)
    write_doc("AGENTS.md", "100 use cases")
    write_doc("docs/PITCH.md", "100 use cases")
    write_doc("docs/architecture.md", "100 use cases")
    assert dc.main([]) == 0


def test_main_missing_doc_files_skipped(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing CHECKS files are silently skipped (no error)."""
    write_content(100)
    assert dc.main([]) == 0
    out = capsys.readouterr().out
    assert "Doc freshness:" in out


# ---------------------------------------------------------------------------
# main() — drift detection
# ---------------------------------------------------------------------------


def test_main_drift_above_tolerance_warns(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Drift > 5% triggers a warning and exit 1."""
    write_content(100)
    write_doc("AGENTS.md", "We have 200 use cases.")
    assert dc.main([]) == 1
    err = capsys.readouterr().err
    assert "Doc freshness: 1 stale count(s)" in err
    assert "AGENTS.md" in err
    assert "claims 200" in err
    assert "actual is 100" in err
    assert ">5% drift" in err


def test_main_drift_below_tolerance_for_low_count(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Claim too low (drift > 5%) also triggers."""
    write_content(100)
    write_doc("AGENTS.md", "We have 50 use cases.")
    assert dc.main([]) == 1
    err = capsys.readouterr().err
    assert "claims 50" in err


def test_main_multiple_docs_all_drifting(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Each drifting doc adds a warning line."""
    write_content(100)
    write_doc("AGENTS.md", "200 use cases")
    write_doc("docs/PITCH.md", "300 use cases")
    write_doc("docs/architecture.md", "400 use cases")
    assert dc.main([]) == 1
    err = capsys.readouterr().err
    assert "3 stale count(s)" in err
    assert "AGENTS.md" in err
    assert "docs/PITCH.md" in err
    assert "docs/architecture.md" in err


def test_main_multiple_matches_in_one_file(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Multiple regex matches in one file each contribute a warning."""
    write_content(100)
    write_doc(
        "AGENTS.md",
        "We have 200 use cases. Or maybe 300 UCs. Definitely 250 use-cases.",
    )
    assert dc.main([]) == 1
    err = capsys.readouterr().err
    assert "3 stale count(s)" in err


def test_main_mixed_passing_and_failing(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Some passing claims + some drifting → only the drifting warn."""
    write_content(100)
    write_doc("AGENTS.md", "100 use cases")
    write_doc("docs/PITCH.md", "300 use cases")
    assert dc.main([]) == 1
    err = capsys.readouterr().err
    assert "1 stale count(s)" in err
    assert "docs/PITCH.md" in err
    assert "AGENTS.md" not in err


def test_main_case_insensitive_pattern(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The `re.IGNORECASE` flag matches `UCS`, `Use Cases`, etc."""
    write_content(100)
    write_doc("AGENTS.md", "We support 200 UCS in our catalog.")
    assert dc.main([]) == 1


# ---------------------------------------------------------------------------
# main() — regex edge cases
# ---------------------------------------------------------------------------


def test_main_unrelated_numbers_not_matched(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Numbers without the `use cases` / `UCs` keyword are not flagged."""
    write_content(100)
    write_doc("AGENTS.md", "Version 3.1.0 released 2026-05-19 with 200 lines.")
    assert dc.main([]) == 0


def test_main_plus_suffix_tolerated(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The `+?` makes the `+` suffix optional but extracts the same group."""
    write_content(100)
    write_doc("AGENTS.md", "100+ use cases AND 100 use cases")
    assert dc.main([]) == 0


def test_main_requires_at_least_two_digits(
    fake_repo: pathlib.Path,
    write_content: WriteContent,
    write_doc: WriteDoc,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The pattern `\\d[\\d,]+` requires 2+ digits, so single digits are not matched."""
    write_content(100)
    write_doc("AGENTS.md", "We have 5 use cases (alpha release).")
    assert dc.main([]) == 0
