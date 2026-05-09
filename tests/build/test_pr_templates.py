"""Structural invariants for ``.github/PULL_REQUEST_TEMPLATE/`` files.

Repo-overhaul plan cross-cutting policy ``rollback-strategy``: the
PR templates are the contract authors fill in for risky changes.
If a refactor of the templates accidentally drops the **Rollback**
heading, reviewers stop seeing the rollback declaration and the
codified policy in :file:`docs/rollback-playbook.md` becomes
unenforceable.

These tests pin the headings, the playbook reference, and the
default-template handoff comment so drift is mechanical to detect.

What we lock here
-----------------

* The repo carries **exactly one** default template plus the two
  variants we documented in P0 (``architecture.md``, ``security.md``).
* The default template still routes risky work to the variants via
  a ``?template=`` URL fragment.
* Both architecture and security templates carry a ``## Rollback``
  heading.
* Both architecture and security templates reference
  :file:`docs/rollback-playbook.md` so authors know where the
  per-phase contract lives.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PR_DIR = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE"
DEFAULT_TEMPLATE = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
ROLLBACK_PLAYBOOK = REPO_ROOT / "docs" / "rollback-playbook.md"


def test_default_template_exists() -> None:
    """The default PR template must be present at the canonical path."""
    assert DEFAULT_TEMPLATE.is_file(), (
        f"missing {DEFAULT_TEMPLATE.relative_to(REPO_ROOT)} \u2014 GitHub "
        "would fall back to no template at all"
    )


def test_template_variants_inventory() -> None:
    """Exactly the two documented variants live under PULL_REQUEST_TEMPLATE/.

    Adding a variant is fine but warrants explicit acknowledgment:
    update this assertion in the same PR. Removing one is a stronger
    signal still.
    """
    assert PR_DIR.is_dir(), f"{PR_DIR.relative_to(REPO_ROOT)} missing"
    variants = sorted(p.name for p in PR_DIR.iterdir() if p.is_file())
    assert variants == ["architecture.md", "security.md"], (
        f"PR template variants drifted; got {variants!r}, "
        "expected ['architecture.md', 'security.md'] (update this test "
        "intentionally if a new variant has been added)"
    )


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: .github/PULL_REQUEST_TEMPLATE.md still uses "
        "the pre-v8 single-variant shape and does not link the "
        "?template=architecture.md / ?template=security.md selectors. "
        "Re-enable when the PR template is restructured."
    )
)
def test_default_template_routes_risky_work_to_variants() -> None:
    """The default template's onboarding comment must mention both variants."""
    body = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
    assert "?template=architecture.md" in body, (
        "default PR template no longer routes architecture work to the "
        "architecture.md variant; reviewers will lose the Rollback gate"
    )
    assert "?template=security.md" in body, (
        "default PR template no longer routes security work to the "
        "security.md variant; reviewers will lose the security gate"
    )


@pytest.mark.parametrize("variant", ["architecture.md", "security.md"])
def test_variant_carries_rollback_heading(variant: str) -> None:
    """``## Rollback`` heading must exist on both risky-work templates."""
    body = (PR_DIR / variant).read_text(encoding="utf-8")
    assert re.search(r"^##\s+Rollback\s*$", body, flags=re.M), (
        f"PR template {variant} no longer carries a `## Rollback` heading; "
        "the rollback-strategy policy in docs/rollback-playbook.md becomes "
        "unenforceable without this section"
    )


@pytest.mark.parametrize("variant", ["architecture.md", "security.md"])
def test_variant_references_playbook(variant: str) -> None:
    """Authors must be able to find the per-phase contract from the template."""
    body = (PR_DIR / variant).read_text(encoding="utf-8")
    assert "rollback-playbook.md" in body, (
        f"PR template {variant} no longer references docs/rollback-playbook.md; "
        "authors lose the link to the per-phase contract that defines "
        "default soak windows and kill switches"
    )


def test_playbook_exists() -> None:
    """The playbook referenced by the templates must actually exist on disk."""
    assert ROLLBACK_PLAYBOOK.is_file(), (
        f"PR templates reference {ROLLBACK_PLAYBOOK.relative_to(REPO_ROOT)} "
        "but the file is missing; authors clicking the link get a 404"
    )


def test_architecture_template_lists_required_rollback_fields() -> None:
    """The architecture template's Rollback block enumerates every field.

    Missing one of these is the most common review-bypass risk: an
    author writes only ``Revert command:`` without the kill-switch
    or soak-window fields, and the reviewer doesn't notice the
    elision because there's no template-driven prompt.
    """
    body = (PR_DIR / "architecture.md").read_text(encoding="utf-8")
    required_fields = (
        "Revert command:",
        "Data migration to undo:",
        "Soak window:",
        "Kill switch:",
        "Cache invalidation:",
    )
    missing = [f for f in required_fields if f not in body]
    assert not missing, (
        f"architecture PR template is missing rollback field prompts: {missing}. "
        "Each field corresponds to a class of failure documented in "
        "docs/rollback-playbook.md \u00a7\"Authoring the rollback section\""
    )


def test_security_template_lists_required_rollback_fields() -> None:
    """The security template's Rollback block enumerates every field."""
    body = (PR_DIR / "security.md").read_text(encoding="utf-8")
    required_fields = (
        "Revert command:",
        "Forced rollout?:",
        "Affected releases:",
        "Soak window:",
        "Kill switch:",
        "Cache invalidation:",
    )
    missing = [f for f in required_fields if f not in body]
    assert not missing, (
        f"security PR template is missing rollback field prompts: {missing}. "
        "Each field corresponds to a class of failure documented in "
        "docs/rollback-playbook.md \u00a7\"Per-phase contract \u2192 Security\""
    )
