"""Structural invariants for :file:`docs/ci-architecture.md`.

Repo-overhaul plan §P2 (2026-05-09): the parallel-job split of
``validate.yml`` is complex enough that future maintainers need a
single page to navigate it. ``docs/ci-architecture.md`` is that
page — it documents the five jobs, the two composite actions, the
ten secondary workflows, and the troubleshooting playbook for each
gate. If the document gets silently rewritten so the partition
mapping vanishes, the maintainer-readable contract is gone.

What we lock here
-----------------

* The doc exists at the canonical path.
* It documents all five parallel jobs from ``validate.yml`` by name.
* It documents both composite actions by path.
* It cross-links to the operational-pair docs so the maintainer
  surface stays discoverable together.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

CI_DOC = REPO_ROOT / "docs" / "ci-architecture.md"

# The five parallel jobs the partition created. Mirrors the pinned
# set in tests/build/test_validate_workflow_partition.py.
EXPECTED_JOBS = ("lint", "audits-content", "audits-build", "mcp", "frontend")

# The two composite actions §P2 introduced.
EXPECTED_COMPOSITES = ("setup-python", "setup-node")

# Cross-references the doc must keep, so the operational pair stays
# discoverable from any of its members.
EXPECTED_REFS = (
    "rollback-playbook.md",
    "external-consumer-matrix.md",
    "capacity-and-staffing.md",
    "SECURITY.md",
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert CI_DOC.is_file(), f"docs/ci-architecture.md missing at {CI_DOC}"
    return CI_DOC.read_text(encoding="utf-8")


def test_doc_exists(doc_text: str) -> None:
    """Sanity-check: the doc has at least the title."""
    assert "# CI Architecture" in doc_text, (
        "docs/ci-architecture.md is missing the canonical ``# CI Architecture`` title."
    )


@pytest.mark.parametrize("job_name", EXPECTED_JOBS)
def test_doc_documents_every_parallel_job(doc_text: str, job_name: str) -> None:
    """Each of the five parallel jobs must be named in the doc.

    The match is intentionally generous (substring, case-sensitive)
    so the doc can describe each job in either prose or table form.
    The invariant is "the job name appears somewhere", not "the
    section is formatted exactly so".
    """
    needle = f"`{job_name}`"
    assert needle in doc_text, (
        f"docs/ci-architecture.md does not name the {job_name!r} job. "
        f"If the partition was renamed, update this test alongside "
        f"tests/build/test_validate_workflow_partition.py."
    )


@pytest.mark.parametrize("composite", EXPECTED_COMPOSITES)
def test_doc_documents_every_composite_action(doc_text: str, composite: str) -> None:
    """Each composite action must be described in the doc."""
    needle = f"setup-{composite.split('-')[1]}/action.yml"
    assert needle in doc_text, (
        f"docs/ci-architecture.md does not describe the composite action "
        f"at .github/actions/{composite}/action.yml. The composite is the "
        f"single point where the underlying SHA is pinned and contributors "
        f"need a navigable description."
    )


@pytest.mark.parametrize("ref", EXPECTED_REFS)
def test_doc_cross_links_operational_pair(doc_text: str, ref: str) -> None:
    """The operational pair (rollback / consumer matrix / capacity / security) must remain linked.

    These docs are best read together; if the link drifts out, a
    contributor lands on one without discovering the others.
    """
    assert ref in doc_text, (
        f"docs/ci-architecture.md no longer references {ref!r}. The four "
        f"operational docs (rollback-playbook, external-consumer-matrix, "
        f"capacity-and-staffing, SECURITY) are designed as a discoverable "
        f"pair from any of their members."
    )


def test_doc_documents_pinning_policy(doc_text: str) -> None:
    """The SHA-pinning rationale must remain in the doc.

    This is the human-readable counterpart to the automated audit at
    ``scripts/audit_action_pins.py``. Without it, future contributors
    will hit the audit failure and not understand why tag-only pins
    are forbidden.
    """
    for needle in (
        "SHA-pinning",
        "Comment drift",
        "Tag-then-force-push",
        "audit_action_pins.py",
    ):
        assert needle in doc_text, (
            f"docs/ci-architecture.md is missing the SHA-pinning rationale "
            f"section (specifically, the {needle!r} keyword). The pinning "
            f"policy is enforced by automation but explained here."
        )


def test_doc_documents_troubleshooting_playbook(doc_text: str) -> None:
    """Every job needs a "when this fails" hint.

    Pure structural test: the substring 'When this job fails' or a
    'Troubleshooting' header signals that the maintainer playbook is
    intact.
    """
    assert "Troubleshooting" in doc_text, (
        "docs/ci-architecture.md is missing the ``## Troubleshooting`` "
        "section. The troubleshooting playbook is the practical payoff "
        "of this doc — without it the page is just a job list."
    )
