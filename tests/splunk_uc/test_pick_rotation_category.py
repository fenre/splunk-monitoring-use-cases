"""Structural tests for ``splunk_uc.tools.pick_rotation_category``.

The picker is the deterministic decision-maker behind the weekly P14
stewardship-rotation reminder. The CI workflow
``.github/workflows/stewardship-rotation.yml`` invokes it once per
ISO week and routes the resulting JSON record into a GitHub issue.

These tests pin three contracts:

1. **Determinism** — ``(iso_week, category-count)`` deterministically
   maps to a single ``cat_num``. Two invocations for the same week
   must return the same category (otherwise issue-deduplication in
   the workflow falls over).
2. **Coverage** — over the 23-week cycle, every category is picked
   exactly once. No silent gaps, no double-picks.
3. **Owner / scorecard wiring** — the helpers that read CODEOWNERS
   and ``dist/scorecard.json`` extract the expected fields without
   relying on regex side-effects or coincidental ordering.

The tests run against the *live* repo state (real CODEOWNERS, real
content/ tree, fixture scorecards built in-test) rather than mocked
versions, because the value of these tests is precisely to catch
drift between the picker logic and the surrounding catalogue
structure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# The ``splunk_uc`` package is not installed; tests add ``src/`` to
# sys.path the same way every other package-level test in the repo
# does (see tests/splunk_uc/test_dispatcher.py for the established
# pattern). pyproject.toml deliberately does not set ``pythonpath``
# here — see the comment block above ``[tool.pytest.ini_options]``.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from splunk_uc.tools.pick_rotation_category import (  # noqa: E402 -- sys.path bootstrap
    EXPECTED_CATEGORY_COUNT,
    _build_record,
    _category_directories,
    _codeowners_owners_for,
    _format_dimensions_table,
    _render_issue_body,
    _rotation_index,
    _scorecard_entry_for,
    main,
)

REPO_ROOT = PROJECT_ROOT


# ---------------------------------------------------------------------------
# Rotation determinism + coverage
# ---------------------------------------------------------------------------


def test_rotation_index_is_deterministic() -> None:
    """``_rotation_index(N)`` returns the same value on repeated calls."""
    for week in (1, 12, 23, 53):
        assert _rotation_index(week) == _rotation_index(week)


def test_rotation_index_cycle_covers_every_category() -> None:
    """Over 23 consecutive weeks the rotation picks every cat exactly once.

    This is the property the workflow relies on for "no category goes
    unnoticed". If the modulo or category count ever drift apart, this
    test will surface it as a missing-or-duplicate slot.
    """
    picks = [_rotation_index(week) for week in range(23)]
    assert sorted(picks) == list(range(23)), (
        f"rotation over 23 consecutive weeks did not cover every category; "
        f"got picks={picks}. Each value 0..22 must appear exactly once."
    )


def test_rotation_index_wraps_cleanly_across_years() -> None:
    """Week 53 falls back into the cycle without dropping a slot."""
    # Week 53 → index 53 % 23 = 7. Week 1 of next year → index 1.
    # The two together span two distinct slots; the property under
    # test is just that the modulo stays well-defined.
    assert _rotation_index(53) == 53 % EXPECTED_CATEGORY_COUNT
    assert 0 <= _rotation_index(53) < EXPECTED_CATEGORY_COUNT


# ---------------------------------------------------------------------------
# Content / CODEOWNERS / scorecard discovery
# ---------------------------------------------------------------------------


def test_category_directories_match_codeowners_rows() -> None:
    """Every content/cat-NN-<slug>/ dir has a matching CODEOWNERS row.

    Mirror of the invariant from ``tests/build/test_codeowners.py``,
    but applied from the picker's vantage so a future change to the
    picker that diverges from the existing CODEOWNERS shape gets
    surfaced here too rather than in a separate test file.
    """
    cats = _category_directories()
    assert len(cats) == EXPECTED_CATEGORY_COUNT, (
        f"expected {EXPECTED_CATEGORY_COUNT} categories, got {len(cats)}; "
        "update EXPECTED_CATEGORY_COUNT in pick_rotation_category.py"
    )

    text = (REPO_ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    for cat_num, slug in cats:
        # Sanity: the integer parsed from the slug matches the cat_num
        # we report back to the workflow.
        assert slug.startswith(f"cat-{cat_num:02d}-"), (
            f"slug {slug!r} does not start with cat-{cat_num:02d}- "
            "(directory-name vs parsed-number drift)"
        )
        # CODEOWNERS lookup returns at least one owner per category.
        owners = _codeowners_owners_for(slug, text)
        assert owners, (
            f"CODEOWNERS has no owner for /content/{slug}/; "
            "the picker would produce an issue with no @-mention"
        )
        for owner in owners:
            assert owner.startswith("@"), f"owner {owner!r} for {slug} does not start with @"


def test_codeowners_parser_handles_multiple_owners() -> None:
    """Multiple owners on one CODEOWNERS line are all returned."""
    text = "# Some comment\n/content/cat-99-test/    @alice @bob-team @carol\n# trailer\n"
    owners = _codeowners_owners_for("cat-99-test", text)
    assert owners == ["@alice", "@bob-team", "@carol"], (
        f"multi-owner parsing failed; got {owners!r}"
    )


def test_codeowners_parser_returns_empty_for_unknown_slug() -> None:
    """An unknown slug returns ``[]`` rather than raising.

    The picker treats an empty owners list as a soft warning so a
    newly added category (CODEOWNERS not yet updated) still produces
    a usable issue body.
    """
    text = "/content/cat-01-server-compute/  @fenre\n"
    assert _codeowners_owners_for("cat-99-not-real", text) == []


def test_scorecard_lookup_works_against_live_scorecard() -> None:
    """The live ``dist/scorecard.json`` resolves every cat 1..23."""
    sc_path = REPO_ROOT / "dist" / "scorecard.json"
    if not sc_path.is_file():
        pytest.skip(
            "dist/scorecard.json not present (run `make build` first); "
            "the CI workflow always builds the scorecard upstream of the picker"
        )
    sc = json.loads(sc_path.read_text(encoding="utf-8"))
    for cat_num in range(1, EXPECTED_CATEGORY_COUNT + 1):
        entry = _scorecard_entry_for(cat_num, sc)
        assert int(entry["cat_num"]) == cat_num
        assert entry.get("name"), f"cat {cat_num}: missing name"
        assert entry.get("composite") is not None, f"cat {cat_num}: missing composite"
        assert entry.get("grade") in {"Bronze", "Silver", "Gold"}, (
            f"cat {cat_num}: unexpected grade {entry.get('grade')!r}"
        )


# ---------------------------------------------------------------------------
# Record + issue-body shape
# ---------------------------------------------------------------------------


def _fixture_scorecard_entry(cat_num: int) -> dict[str, object]:
    """A minimal scorecard entry suitable for record-shape tests."""
    return {
        "cat_num": str(cat_num),
        "name": "Test Category",
        "uc_count": 10,
        "security_count": 4,
        "composite": 75.5,
        "grade": "Silver",
        "content_depth": 70.0,
        "references_pct": 100.0,
        "kfp_pct": 95.0,
        "mitre_pct": 50.0,
        "freshness_score": 80.0,
        "freshness_median_days": 14.0,
        "provenance_authority": 90.0,
        "samples_pct": 12.5,
        "depth_tier_distribution": {"silver": 8, "bronze": 2},
        "status_distribution": {"verified": 7, "draft": 3},
        "origin_distribution": {"splunk-official": 9, "contributor": 1},
    }


def test_build_record_includes_required_workflow_fields() -> None:
    """The record carries every field the workflow renders into the issue."""
    record = _build_record(
        iso_year=2026,
        iso_week=5,
        cat_num=3,
        slug="cat-03-containers-orchestration",
        owners=["@fenre"],
        scorecard_entry=_fixture_scorecard_entry(3),
    )
    expected_keys = {
        "iso_year",
        "iso_week",
        "rotation_index",
        "cat_num",
        "slug",
        "name",
        "composite",
        "grade",
        "uc_count",
        "security_count",
        "owners",
        "drilldown",
        "codeowners_row",
        "content_dir",
        "dimensions",
        "depth_tier_distribution",
        "status_distribution",
        "origin_distribution",
    }
    missing = expected_keys - set(record.keys())
    assert not missing, f"record is missing required keys: {missing}"
    assert record["rotation_index"] == _rotation_index(5)
    assert record["drilldown"] == "docs/scorecard.md#cat-03-containers-orchestration"
    assert record["codeowners_row"] == "/content/cat-03-containers-orchestration/"
    assert record["content_dir"] == "content/cat-03-containers-orchestration/"


def test_dimensions_table_renders_seven_rows() -> None:
    """The rendered dimensions table has the 7 scorecard dimensions."""
    table = _format_dimensions_table(
        {
            "content_depth": 70.0,
            "references_pct": 100.0,
            "kfp_pct": 95.0,
            "mitre_pct": 50.0,
            "freshness_score": 80.0,
            "provenance_authority": 90.0,
            "samples_pct": 12.5,
        }
    )
    # 2 header rows + 7 data rows = 9 lines.
    assert len(table.splitlines()) == 9
    assert "Content depth" in table
    assert "MITRE ATT&CK coverage" in table
    assert "Sample fixtures" in table


def test_issue_body_links_to_scorecard_drilldown_and_owners() -> None:
    """Issue body has owner @-mentions, drilldown URL, and stewardship checklist."""
    record = _build_record(
        iso_year=2026,
        iso_week=5,
        cat_num=3,
        slug="cat-03-containers-orchestration",
        owners=["@fenre", "@security-team"],
        scorecard_entry=_fixture_scorecard_entry(3),
    )
    body = _render_issue_body(
        record,
        repo_url_base="https://github.com/example/repo/blob/main",
    )
    assert "@fenre" in body, "owner @-mention missing from issue body"
    assert "@security-team" in body, "second owner missing from issue body"
    assert (
        "https://github.com/example/repo/blob/main/docs/scorecard.md#cat-03-containers-orchestration"
        in body
    ), "scorecard drilldown URL missing"
    assert (
        "https://github.com/example/repo/blob/main/content/cat-03-containers-orchestration/" in body
    ), "content directory URL missing"
    assert "ISO 2026-W05" in body, "week tag missing from issue body"
    assert "### Suggested stewardship review" in body, "stewardship checklist missing"
    assert "Auto-generated by `.github/workflows/stewardship-rotation.yml`" in body


def test_issue_body_handles_no_codeowners_owner() -> None:
    """A category with no CODEOWNERS row gets a graceful inline notice."""
    record = _build_record(
        iso_year=2026,
        iso_week=5,
        cat_num=99,
        slug="cat-99-not-yet-onboarded",
        owners=[],
        scorecard_entry=_fixture_scorecard_entry(99),
    )
    body = _render_issue_body(
        record,
        repo_url_base="https://github.com/example/repo/blob/main",
    )
    assert "no CODEOWNERS owner found" in body, (
        "missing-owner notice should mention how to fix the CODEOWNERS gap"
    )


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def test_main_emits_json_for_explicit_week(capsys: pytest.CaptureFixture[str]) -> None:
    """``main(['--week','5','--year','2026'])`` returns 0 and emits parseable JSON."""
    sc_path = REPO_ROOT / "dist" / "scorecard.json"
    if not sc_path.is_file():
        pytest.skip("dist/scorecard.json not present; run `make build` first")
    rc = main(["--week", "5", "--year", "2026"])
    assert rc == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["iso_week"] == 5
    assert payload["iso_year"] == 2026
    assert payload["rotation_index"] == 5 % EXPECTED_CATEGORY_COUNT
    assert 1 <= payload["cat_num"] <= EXPECTED_CATEGORY_COUNT


def test_main_rejects_invalid_week(capsys: pytest.CaptureFixture[str]) -> None:
    """Out-of-range ``--week`` is rejected with a non-zero exit code."""
    rc = main(["--week", "0", "--year", "2026"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "--week" in err, "the error message should call out --week"


def test_main_writes_issue_body_to_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--write-issue-body`` populates the target file with valid markdown."""
    sc_path = REPO_ROOT / "dist" / "scorecard.json"
    if not sc_path.is_file():
        pytest.skip("dist/scorecard.json not present; run `make build` first")
    out = tmp_path / "subdir" / "issue.md"
    rc = main(["--week", "5", "--year", "2026", "--write-issue-body", str(out)])
    assert rc == 0
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert body.startswith("## Category "), "issue body should open with a level-2 category heading"
    assert re.search(r"ISO 2026-W05", body), "week tag missing"
    assert body.endswith("\n"), "issue body should end with a single trailing newline"
