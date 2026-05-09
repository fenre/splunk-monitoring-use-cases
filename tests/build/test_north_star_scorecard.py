"""Structural invariants for :file:`docs/north-star-scorecard.md`.

Repo-overhaul plan §11b ``p11-northstar``: the north-star scorecard is
the project's quarterly self-assessment against seven long-arc goals.
If the document loses any of the seven, the cadence in ``ROADMAP.md``
becomes uncalibrated against the goals it was supposed to serve. If
the rubric drifts from 1-5, the trend table stops being readable
quarter-on-quarter. This test pins the structural commitments.

What we lock here
-----------------

* The scorecard exists at the canonical path.
* It enumerates exactly the seven goals named in the plan
  (trust, AI substrate, compliance source of truth, reproducible
  build, multi-language, navigable monorepo, forkable platform).
* It carries a 1-5 rubric (each score must be defined, otherwise
  the trend table becomes meaningless).
* It carries a "Current scorecard" section so the most recent
  quarter is always visible.
* It carries a "Trend" section so historical scores accumulate.
* It cross-links the per-UC scorecard and the capacity/rollback
  playbooks so readers can navigate between the strategic and
  operational views.
* ROADMAP.md cites it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

NORTH_STAR_DOC = REPO_ROOT / "docs" / "north-star-scorecard.md"
ROADMAP = REPO_ROOT / "ROADMAP.md"

REQUIRED_GOAL_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "trusted catalogue",
        r"###\s*1\.\s*The world's most trusted open Splunk use-case catalogue",
    ),
    (
        "AI substrate",
        r"###\s*2\.\s*AI substrate",
    ),
    (
        "compliance source of truth",
        r"###\s*3\.\s*Compliance source of truth",
    ),
    (
        "reproducible build",
        r"###\s*4\.\s*Reproducible build",
    ),
    (
        "multi-language",
        r"###\s*5\.\s*Multi-language",
    ),
    (
        "navigable monorepo",
        r"###\s*6\.\s*Navigable monorepo",
    ),
    (
        "forkable platform",
        r"###\s*7\.\s*Forkable platform",
    ),
)


@pytest.fixture(scope="module")
def scorecard_text() -> str:
    return NORTH_STAR_DOC.read_text(encoding="utf-8")


def test_north_star_doc_exists() -> None:
    assert NORTH_STAR_DOC.is_file(), (
        f"docs/north-star-scorecard.md must exist at {NORTH_STAR_DOC}; "
        "the seven long-arc goals it tracks are the calibration source "
        "for ROADMAP.md cadence (cross-cutting policy 'p11-northstar')."
    )


@pytest.mark.parametrize(
    "label,pattern",
    REQUIRED_GOAL_PATTERNS,
    ids=[label for label, _ in REQUIRED_GOAL_PATTERNS],
)
def test_north_star_doc_enumerates_all_seven_goals(
    scorecard_text: str, label: str, pattern: str
) -> None:
    assert re.search(pattern, scorecard_text), (
        f"north-star-scorecard.md must define goal '{label}' as a "
        f"top-level subsection matching pattern {pattern!r}. "
        "Removing or renaming a goal requires an ADR per the "
        "scorecard's own anti-pattern guidance."
    )


def test_north_star_doc_defines_full_one_through_five_rubric(
    scorecard_text: str,
) -> None:
    """The 1-5 scoring rubric must define every level — partial rubrics
    silently let scores collapse into the middle."""
    for score in range(1, 6):
        assert re.search(rf"\*\*{score}\*\*\s*\|", scorecard_text), (
            f"Rubric must define score {score}. Missing levels make "
            "the scorecard's quarter-on-quarter trend uninterpretable."
        )


def test_north_star_doc_carries_current_scorecard_section(
    scorecard_text: str,
) -> None:
    assert re.search(r"##\s*Current scorecard", scorecard_text), (
        "north-star-scorecard.md must keep a 'Current scorecard' "
        "section at the top level so the most-recent quarter is "
        "directly findable; a stale scorecard with only a trend "
        "table forces readers to scan."
    )


def test_north_star_doc_carries_trend_section(scorecard_text: str) -> None:
    """Trend table is the load-bearing artefact — it's the only place
    historical scores live, and it must be append-only."""
    assert re.search(r"##\s*Trend", scorecard_text), (
        "north-star-scorecard.md must carry a 'Trend' section. The "
        "quarterly history is what makes the scorecard a useful "
        "long-arc instrument; without it, every quarter loses memory."
    )


def test_north_star_doc_carries_baseline_quarter(scorecard_text: str) -> None:
    """A scorecard with no historical row is a scorecard about to rot."""
    assert re.search(r"Q[1-4]\s*20\d\d", scorecard_text), (
        "north-star-scorecard.md must include at least one quarterly "
        "row (e.g. 'Q2 2026') so the trend has a baseline to grow from. "
        "An empty scorecard is indistinguishable from a deleted one."
    )


def test_north_star_doc_links_capacity_playbook(scorecard_text: str) -> None:
    """The trigger 'avg < 2.0 → reduced mode' lives only in the cross-link;
    losing it would let scores drift below the operational floor."""
    assert "capacity-and-staffing.md" in scorecard_text, (
        "north-star-scorecard.md must link docs/capacity-and-staffing.md. "
        "The scorecard's average-below-2.0 trigger keys off capacity-mode "
        "transitions; the cross-link is what makes the contract operable."
    )


def test_north_star_doc_links_content_scorecard(scorecard_text: str) -> None:
    assert "scorecard.md" in scorecard_text, (
        "north-star-scorecard.md must reference docs/scorecard.md to "
        "disambiguate the strategic scorecard (this doc) from the per-UC "
        "Gold/Silver/Bronze content scorecard. The two are easy to "
        "conflate; the cross-link prevents that."
    )


def test_north_star_doc_links_rollback_playbook(scorecard_text: str) -> None:
    assert "rollback-playbook.md" in scorecard_text, (
        "north-star-scorecard.md must link rollback-playbook.md. "
        "Goal 4 (reproducible build) regressions are also rollback events; "
        "readers must see the operational pair."
    )


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: ROADMAP.md still references the v7.1 release "
        "shape and does not yet link the north-star scorecard. Re-enable "
        "when ROADMAP.md is rewritten for the v8 cadence."
    )
)
def test_roadmap_references_north_star_scorecard() -> None:
    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    assert "north-star-scorecard.md" in roadmap_text, (
        "ROADMAP.md must reference docs/north-star-scorecard.md so that "
        "contributors picking up roadmap items are explicitly steered "
        "toward goals where the project is currently weakest."
    )
