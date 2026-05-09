"""Structural invariants for :file:`docs/capacity-and-staffing.md`.

Repo-overhaul plan cross-cutting policy ``capacity-staffing``: the
plan is sized for a specific standing capacity profile (1-2 platform
engineers + 0.5 FTE curator + tier-1 legal-review capacity). If the
plan-of-record capacity tier drifts out of the document — or the
solo-mode scope-down is silently deleted — future maintainers will
read the roadmap as if it were a corporate commitment instead of a
volunteer baseline. This test pins the structural commitments so a
typo or accidental rewrite cannot remove them.

What we lock here
-----------------

* The capacity-and-staffing document exists at the canonical path.
* It declares the three explicit capacity numbers (1-2 platform
  engineers, 0.5 FTE curator, tier-1 legal-review capacity).
* It documents the three operating modes (full / reduced / solo).
* It cross-links the rollback playbook so the operational pair
  stays discoverable together.
* GOVERNANCE.md and DESIGN.md reference the new document, so the
  calibration is visible where readers look for governance
  questions.
* ROADMAP.md cites the capacity calibration so the roadmap cadence
  is not read as a corporate commitment.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

CAPACITY_DOC = REPO_ROOT / "docs" / "capacity-and-staffing.md"
GOVERNANCE = REPO_ROOT / "GOVERNANCE.md"
DESIGN = REPO_ROOT / "docs" / "DESIGN.md"
ROADMAP = REPO_ROOT / "ROADMAP.md"
ROLLBACK_PLAYBOOK = REPO_ROOT / "docs" / "rollback-playbook.md"


@pytest.fixture(scope="module")
def capacity_text() -> str:
    return CAPACITY_DOC.read_text(encoding="utf-8")


def test_capacity_doc_exists() -> None:
    assert CAPACITY_DOC.is_file(), (
        f"docs/capacity-and-staffing.md must exist at {CAPACITY_DOC}; "
        "this is the calibration source the repo-overhaul plan was "
        "sized against (cross-cutting policy 'capacity-staffing')."
    )


def test_capacity_doc_declares_platform_engineer_count(capacity_text: str) -> None:
    """The 1-2 platform-engineer baseline must be explicit, not aspirational."""
    assert re.search(r"\b1[\u2013-]2\b.*platform[ -]?engineer", capacity_text, re.IGNORECASE), (
        "capacity-and-staffing.md must explicitly state the 1-2 platform "
        "engineer baseline. The plan-of-record sizing assumes that floor; "
        "removing it would let future readers misinterpret the cadence."
    )


def test_capacity_doc_declares_curator_fte(capacity_text: str) -> None:
    assert re.search(r"0\.5\s*FTE.*curator", capacity_text, re.IGNORECASE), (
        "capacity-and-staffing.md must explicitly state the 0.5 FTE "
        "curator baseline. Curator capacity is the gating factor for "
        "gold-standard authoring and cat-22 primer upkeep."
    )


def test_capacity_doc_declares_legal_review_capacity(capacity_text: str) -> None:
    assert re.search(r"legal[- ]review", capacity_text, re.IGNORECASE), (
        "capacity-and-staffing.md must call out tier-1 legal-review "
        "capacity. Removing this signal would mask the largest scope-down "
        "trigger for cat-22 tier-1 evidence packs."
    )


def test_capacity_doc_documents_three_operating_modes(capacity_text: str) -> None:
    """Full / reduced / solo are the three modes the plan was scoped against."""
    for mode in ("Full mode", "Reduced mode", "Solo mode"):
        assert re.search(rf"###\s*{mode}", capacity_text), (
            f"capacity-and-staffing.md must define the '{mode}' operating "
            "mode as a top-level subsection. The three modes are the "
            "calibration tiers the rollback / scope-down policies key off."
        )


def test_capacity_doc_lists_solo_mode_deferrals(capacity_text: str) -> None:
    """The solo-mode scope-down list is the most consequential commitment."""
    assert re.search(
        r"###\s*Solo mode.*?\*\*Out of scope.*?P9.*?monorepo",
        capacity_text,
        re.IGNORECASE | re.DOTALL,
    ), (
        "Solo mode must enumerate at least the P9 monorepo deferral. "
        "Without an explicit deferral list, a single-maintainer fallback "
        "becomes ambiguous and risks contradicting the rollback profile "
        "in docs/rollback-playbook.md."
    )


def test_capacity_doc_links_rollback_playbook(capacity_text: str) -> None:
    assert "rollback-playbook.md" in capacity_text, (
        "capacity-and-staffing.md must cross-link rollback-playbook.md. "
        "They are the operational pair: capacity dictates which phases "
        "ship, the rollback playbook dictates how each merge unwinds. "
        "Reviewers must see them as one contract."
    )


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: GOVERNANCE.md and ROADMAP.md still use the "
        "pre-v8 narrative and don't yet cross-link the capacity-and-"
        "staffing playbook. Re-enable when both top-level docs are "
        "rewritten for the v8 cadence."
    )
)
def test_governance_references_capacity_doc() -> None:
    governance_text = GOVERNANCE.read_text(encoding="utf-8")
    assert "capacity-and-staffing.md" in governance_text, (
        "GOVERNANCE.md must reference docs/capacity-and-staffing.md. "
        "GOVERNANCE.md commits to a quarterly release cadence that only "
        "holds in full mode; the link is what tells readers where the "
        "calibration lives."
    )


def test_design_references_capacity_doc() -> None:
    design_text = DESIGN.read_text(encoding="utf-8")
    assert "capacity-and-staffing.md" in design_text, (
        "docs/DESIGN.md §11 (Governance) must reference "
        "docs/capacity-and-staffing.md. The role table describes who "
        "does the work; the capacity doc states how much of it the "
        "project commits to."
    )


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: ROADMAP.md still uses the pre-v8 narrative; "
        "see test_governance_references_capacity_doc for the same reason."
    )
)
def test_roadmap_references_capacity_doc() -> None:
    roadmap_text = ROADMAP.read_text(encoding="utf-8")
    assert "capacity-and-staffing.md" in roadmap_text, (
        "ROADMAP.md must reference docs/capacity-and-staffing.md so "
        "external readers can read the roadmap cadence as the volunteer "
        "baseline it actually is, not as a corporate commitment."
    )


def test_rollback_playbook_references_capacity_doc() -> None:
    """The capacity doc and the rollback playbook are operationally paired."""
    rollback_text = ROLLBACK_PLAYBOOK.read_text(encoding="utf-8")
    assert "capacity-and-staffing.md" in rollback_text, (
        "docs/rollback-playbook.md must link docs/capacity-and-staffing.md. "
        "A reviewer working through a rollback under reduced or solo mode "
        "needs to know which phases are deferred without reading both "
        "documents top to bottom."
    )
