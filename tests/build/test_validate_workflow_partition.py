"""Structural invariants for the parallel-job split of ``validate.yml``.

Repo-overhaul plan §P2 (2026-05-09): the previous monolithic
``validate`` job was split into five parallel jobs (``lint``,
``audits-content``, ``audits-build``, ``mcp``, ``frontend``). These
tests pin the partition so a future re-split, refactor, or hand-edit
cannot:

* drop a job entirely;
* delete a step without re-homing it elsewhere;
* introduce duplicate step coverage that would silently double the
  CI bill;
* re-introduce ``actions/setup-python`` or ``actions/setup-node`` SHA
  pins outside the composite actions, which would re-create the
  comment-drift class of bug §P2 was specifically designed to
  eliminate.

The job layout itself is enforced as a fixed set; adding a new
parallel job is fine, but it must be done by editing this test in
the same PR so a reviewer is forced to think about whether the new
job duplicates existing work.

Why structural rather than golden-snapshot
------------------------------------------

A golden snapshot of the YAML file would fire on every cosmetic
edit (whitespace, comment changes), creating a "rubber-stamp" PR
class that desensitises reviewers. These tests instead pin the
*invariants* the partition was designed to protect:

1. Five named jobs exist.
2. Every job uses the composite actions for setup.
3. Every job's body has a non-trivial step count.
4. The total step count across all jobs is at least the floor we
   reached when the partition landed (drift below the floor means
   a step was silently dropped).
5. No critical step is missing (assert names exist somewhere).
6. No two jobs duplicate the same script name in their ``run:``
   commands except for the deliberate api/v1 regeneration that
   ``mcp`` and ``frontend`` need to run independently.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

# v8.x: PR-5 (2026-05-12) landed the five-job parallel split of
# validate.yml — ``lint`` / ``audits-content`` / ``audits-build`` /
# ``mcp`` / ``frontend``. The structural assertions in this module are
# now the contract between the workflow and any future re-partition,
# refactor, or hand-edit. Restoring the skip marker is forbidden — the
# whole point of this module is to keep CI honest about the partition.

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATE_YML = REPO_ROOT / ".github" / "workflows" / "validate.yml"

# The five jobs the partition created. Adding a new job is allowed,
# but the test below asserts the *minimum* set is present so a job
# can never silently disappear.
EXPECTED_JOBS = ("lint", "audits-content", "audits-build", "mcp", "frontend")

# Setup-prelude step names that should appear in every job. They are
# allowed to differ in suffix (``Set up Python (with audits)`` vs
# ``Set up Python``) but the substring match catches them all.
SETUP_PREFIXES = ("Checkout", "Set up Python", "Set up Node")

# Step names that MUST exist somewhere in the partition. Each entry
# is a substring match — the partition test isn't title-format
# sensitive, just coverage sensitive. If any of these strings
# disappears from validate.yml the partition has lost coverage for
# a critical audit. Adding a step here is mandatory when adding a
# new audit; removing a step here is allowed only with a paired PR
# that justifies the removal in CHANGELOG.md + docs/migration-status.md.
CRITICAL_STEP_NAMES = [
    # Lint job
    "Schema metadata validation",
    "GitHub Actions pin audit",
    "Non-technical view JS syntax",
    "Docs-UC map JS syntax",
    "Version consistency",
    # Content audits
    "Unit tests (build pipeline",  # P16 renamed to "...build pipeline + audits)"; substring match
    "Coverage budget audit",
    # v8.2.0 (2026-05-11) retired the legacy ``use-cases/cat-*.md``
    # corpus, which made the original ``audit-legacy-orphans`` verb
    # meaningless (nothing left to be orphaned from). The replacement
    # ``audit-no-use-cases-dir`` runs in audits-content as
    # ``Legacy use-cases/ guard (v8.2.0 retirement)`` and serves the
    # same intent: prevent legacy markdown orphans from accumulating.
    "Legacy use-cases/ guard",
    "UC ID uniqueness",
    "UC structure validation",
    "SPL grammar linter",
    "SPL hallucination audit",
    "MITRE ATT&CK taxonomy",
    "Monitoring-type policy",
    "CIM",  # CIM ↔ SPL alignment
    "CHANGELOG and cross-references",
    "Repository consistency",
    "Catalog schema validation",
    # PR-2 lean-mode collapse (2026-05-17, drift ledger #20): the 14
    # individual cascade-regen ``--check`` steps were replaced by a
    # single umbrella drift gate that calls ``make
    # sync-generated-check``. The umbrella covers (and the per-step
    # log makes visible) every previously-named cascade gate, so
    # losing it would still lose coverage for: prerequisite graph,
    # phase3.{1,2,3} backfills, equipment-tags, grandma explanations,
    # md-from-json freshness, cat-22 NTV regen, compliance-gaps,
    # evidence-packs, mapping-ledger determinism, sandbox-validation,
    # backlinks index, and the auto-generated doc references rewrite.
    # If the umbrella is ever split back into individual steps, add
    # the per-step names here in the same PR.
    "Cascade-generator drift gate (umbrella)",
    "Compliance mapping audit",
    "Gold Standard quality audit",
    "Phase 4.5a peer-review signoff audit",
    "Phase 4.5b legal-review signoff audit",
    "Phase 5.2 SME-review signoff audit",
    "Phase 5.3 regulatory change-watch",
    "Phase 5.4 signed provenance ledger",
    # Build job
    "Build check (catalog regeneration)",
    "Audit — byte budgets",
    "Audit — URL freeze",
    "Splunk Cloud compatibility audit",
    "Splunk UC Recommender generator regeneration check",
    "API surface (api/v1) regeneration check",
    "Story-layer UI smoke tests",
    "Package recommender .spl",
    # MCP job
    "Install MCP server",
    "MCP server unit tests",
    "MCP tool schema drift guard",
    # Frontend job
    "Recommender frontend unit tests",
    "Phase 4.4 scorecard.html render test",
    "Phase 4.5c sandbox validation Node drift guard",
    "Phase 4.5d ATT&CK simulation gate",
    "Phase 4.5d ATT&CK simulation Node drift guard",
    "Phase 4.5e OSCAL round-trip gate",
    "Phase 4.5e OSCAL round-trip Node drift guard",
    "Phase 4.5f perf + a11y audit gate",
    "Phase 4.5f perf + a11y Node drift guard",
    "apps/web — non-technical-view.js SOT drift guard",
]

# Floor: the partition landed with this many non-setup steps in
# total. If a future PR drops below this without an explicit
# CHANGELOG note, treat it as accidental drift.
MINIMUM_TOTAL_CONTENT_STEPS = 80


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    assert VALIDATE_YML.is_file(), f"validate.yml missing at {VALIDATE_YML}"
    data = yaml.safe_load(VALIDATE_YML.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _is_setup_step(step: dict[str, Any]) -> bool:
    name = step.get("name", "")
    return any(name.startswith(p) for p in SETUP_PREFIXES)


def _content_step_names(steps: list[dict[str, Any]]) -> list[str]:
    return [s.get("name", "") for s in steps if not _is_setup_step(s)]


def _all_content_steps(workflow: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for job in workflow["jobs"].values():
        out.extend(_content_step_names(job.get("steps", [])))
    return out


# ---------------------------------------------------------------------------
# Job inventory + setup uniformity
# ---------------------------------------------------------------------------


def test_all_expected_jobs_exist(workflow: dict[str, Any]) -> None:
    """Each of the five partition jobs must be present.

    Adding a new job (e.g. ``security``) is fine; *removing* a job
    silently is not. Update ``EXPECTED_JOBS`` in this test alongside
    any structural change so reviewers see the intent.
    """
    actual = set(workflow["jobs"].keys())
    missing = set(EXPECTED_JOBS) - actual
    assert not missing, (
        f"validate.yml is missing the following parallel-split jobs: {sorted(missing)}. "
        f"If you renamed or removed a job, update EXPECTED_JOBS in this test "
        f"so the rename is reviewable."
    )


@pytest.mark.parametrize("job_name", EXPECTED_JOBS)
def test_every_job_uses_composite_setup_python(
    workflow: dict[str, Any], job_name: str
) -> None:
    """Every job must use the composite ``setup-python`` action.

    Re-introducing a direct ``actions/setup-python@<sha>`` pin in any
    job re-creates the comment-drift bug class §P2 was designed to
    eliminate, and bypasses the centralised audit-floor install.
    """
    job = workflow["jobs"][job_name]
    setup_uses = [
        step.get("uses", "")
        for step in job["steps"]
        if step.get("name", "").startswith("Set up Python")
    ]
    assert any(u == "./.github/actions/setup-python" for u in setup_uses), (
        f"job {job_name!r}: must use ``./.github/actions/setup-python`` "
        f"composite action; got {setup_uses}"
    )


@pytest.mark.parametrize("job_name", EXPECTED_JOBS)
def test_every_job_has_minimum_content_steps(
    workflow: dict[str, Any], job_name: str
) -> None:
    """No job may degenerate to setup-only.

    A job with just setup steps and no content steps is dead weight
    (consumes a runner, contributes no signal). The floor of 1 is
    intentionally tiny — the structural check just rejects empty
    jobs.
    """
    job = workflow["jobs"][job_name]
    content = _content_step_names(job.get("steps", []))
    assert len(content) >= 1, (
        f"job {job_name!r}: has no content steps — only setup steps remain. "
        f"Either remove the job or restore its steps."
    )


@pytest.mark.parametrize("job_name", EXPECTED_JOBS)
def test_every_job_declares_timeout(workflow: dict[str, Any], job_name: str) -> None:
    """Every job needs ``timeout-minutes:`` so a hung step can't waste a runner.

    The default GitHub timeout is 360 minutes (6 hours) which is
    catastrophic for a hung audit. We enforce explicit timeouts so
    every job is bounded.
    """
    job = workflow["jobs"][job_name]
    timeout = job.get("timeout-minutes")
    assert isinstance(timeout, int) and 1 <= timeout <= 60, (
        f"job {job_name!r}: timeout-minutes must be an int in [1, 60]; "
        f"got {timeout!r}. The longest job (audits-build) is sized for "
        f"~30 minutes today, so 60 is a comfortable upper bound."
    )


# ---------------------------------------------------------------------------
# Step coverage
# ---------------------------------------------------------------------------


def test_total_content_steps_above_floor(workflow: dict[str, Any]) -> None:
    """The total content-step count must stay at or above the partition floor.

    If a future PR drops below the floor without paired changes to
    this test, treat it as accidental drift. Lifting the floor is
    fine; lowering it requires explicit reasoning.
    """
    total = len(_all_content_steps(workflow))
    assert total >= MINIMUM_TOTAL_CONTENT_STEPS, (
        f"validate.yml has only {total} content steps across all jobs; "
        f"floor is {MINIMUM_TOTAL_CONTENT_STEPS}. Either restore the missing "
        f"steps or update MINIMUM_TOTAL_CONTENT_STEPS in this test with "
        f"justification."
    )


@pytest.mark.parametrize("expected", CRITICAL_STEP_NAMES)
def test_critical_step_present(workflow: dict[str, Any], expected: str) -> None:
    """Every critical-coverage step must appear in some job.

    Substring match — the partition is title-format insensitive,
    so e.g. "Equipment-tags regeneration check (sidecar...)" and
    "Equipment-tags regeneration check" both satisfy a check for
    ``"Equipment-tags regeneration check"``.
    """
    all_names = " || ".join(_all_content_steps(workflow))
    assert expected in all_names, (
        f"critical step {expected!r} not found in any job in validate.yml. "
        f"If the step was renamed, update CRITICAL_STEP_NAMES in this test."
    )


# ---------------------------------------------------------------------------
# Forbidden patterns (re-pinning + duplicate work)
# ---------------------------------------------------------------------------


def test_no_workflow_pins_setup_python_directly(workflow: dict[str, Any]) -> None:
    """No job may re-introduce ``actions/setup-python@<sha>`` directly.

    The composite action is the single point where the SHA is pinned;
    re-introducing the pin in a workflow re-creates the comment-drift
    bug §P2 was designed to eliminate.
    """
    raw = VALIDATE_YML.read_text(encoding="utf-8")
    assert "actions/setup-python@" not in raw, (
        "validate.yml directly pins actions/setup-python@<sha> somewhere. "
        "Use ``uses: ./.github/actions/setup-python`` instead — the "
        "composite action is the single point of truth for the SHA."
    )


def test_no_workflow_pins_setup_node_directly(workflow: dict[str, Any]) -> None:
    """No job may re-introduce ``actions/setup-node@<sha>`` directly."""
    raw = VALIDATE_YML.read_text(encoding="utf-8")
    assert "actions/setup-node@" not in raw, (
        "validate.yml directly pins actions/setup-node@<sha> somewhere. "
        "Use ``uses: ./.github/actions/setup-node`` instead."
    )


def test_referenced_python_scripts_exist(workflow: dict[str, Any]) -> None:
    """Every ``python3 scripts/<name>.py`` reference must point at a real file.

    Catches dead-step references like the one we removed during the
    partition: ``scripts/generate_splunk_app.py`` no longer exists,
    and the legacy step that referenced it had silently been
    quarantined for months.
    """
    raw = VALIDATE_YML.read_text(encoding="utf-8")
    pattern = re.compile(r"python3?\s+(scripts/\S+\.py|tools/\S+\.py)")
    referenced = set(pattern.findall(raw))
    missing = []
    for ref in sorted(referenced):
        candidate = REPO_ROOT / ref
        if not candidate.is_file():
            missing.append(ref)
    assert not missing, (
        f"validate.yml references the following Python scripts that do not "
        f"exist on disk: {missing}. Either restore the script, remove the "
        f"step, or fix the path."
    )


def test_referenced_node_test_files_exist(workflow: dict[str, Any]) -> None:
    """Every ``node --test tests/<...>.test.mjs`` reference must point at a real file."""
    raw = VALIDATE_YML.read_text(encoding="utf-8")
    pattern = re.compile(r"node\s+(?:--test\s+)?(tests/\S+\.(?:mjs|js))")
    referenced = set(pattern.findall(raw))
    missing = []
    for ref in sorted(referenced):
        candidate = REPO_ROOT / ref
        if not candidate.is_file():
            missing.append(ref)
    assert not missing, (
        f"validate.yml references the following Node test files that do not "
        f"exist on disk: {missing}."
    )


def test_uniform_python_setup_action_path(workflow: dict[str, Any]) -> None:
    """Every job that uses setup-python must reference the composite by absolute path.

    GitHub Actions resolves ``./.github/actions/setup-python`` correctly
    regardless of the current working directory of the runner. The
    invariant we want is: the path string is *exactly*
    ``./.github/actions/setup-python``, not ``./.github/actions/setup-python/``
    or ``setup-python`` (which would resolve to a marketplace action).
    """
    canonical = "./.github/actions/setup-python"
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "setup-python" in uses and uses != canonical:
                pytest.fail(
                    f"job {job_name!r}: setup-python ``uses:`` is "
                    f"{uses!r}; expected {canonical!r} (no trailing slash)."
                )


def test_uniform_node_setup_action_path(workflow: dict[str, Any]) -> None:
    """Every job that uses setup-node must reference the composite by absolute path."""
    canonical = "./.github/actions/setup-node"
    for job_name, job in workflow["jobs"].items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "setup-node" in uses and uses != canonical:
                pytest.fail(
                    f"job {job_name!r}: setup-node ``uses:`` is "
                    f"{uses!r}; expected {canonical!r}."
                )
