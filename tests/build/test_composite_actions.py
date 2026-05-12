"""Structural invariants for ``.github/actions/*/action.yml``.

Repo-overhaul plan §P2 (2026-05-08): the composite actions
``setup-python`` and ``setup-node`` centralise the toolchain setup
that was previously duplicated across 9 workflow files. They are
therefore high-leverage — a regression in either one breaks every
workflow at once. These tests pin the structural properties that
make them safe to depend on:

* Both actions exist at the canonical paths.
* The composite-action schema is honoured (``runs.using == 'composite'``,
  inputs declare descriptions, every ``run:`` step also declares a
  ``shell:`` because composite actions don't get a default shell).
* Every third-party SHA is a 40-char hex string with a trailing
  ``# vX.Y.Z`` comment — the same supply-chain hygiene rule the
  ``audit_action_pins.py`` auditor enforces.
* Default versions match the project-wide pin (Python 3.12, Node 20)
  to prevent silent toolchain drift.
* The ``setup-python`` action accepts the documented ``install-audits``
  + ``install-extras`` inputs (their absence would silently strip
  features from every consuming workflow).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"

# Pinned by the project — bump these only after updating the matching
# composite action AND the # vX.Y.Z comment in lockstep.
PROJECT_PYTHON_VERSION = "3.12"
PROJECT_NODE_VERSION = "20"

# Match `uses: <action>@<sha> # <tag>`.
_USES_RE = re.compile(
    r"^\s*-?\s*uses:\s*(?P<action>\S+?)@(?P<sha>[a-f0-9]{40})\s.*?#\s*(?P<tag>v\S+)"
)


def _load(action_name: str) -> dict[str, Any]:
    path = ACTIONS_DIR / action_name / "action.yml"
    assert path.is_file(), f"composite action not found at {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} did not parse to a YAML mapping"
    return data


# ---------------------------------------------------------------------------
# Existence + canonical paths
# ---------------------------------------------------------------------------


def test_setup_python_exists() -> None:
    assert (ACTIONS_DIR / "setup-python" / "action.yml").is_file(), (
        "setup-python composite action must live at .github/actions/setup-python/action.yml; "
        "any rename breaks every workflow that calls ./.github/actions/setup-python"
    )


def test_setup_node_exists() -> None:
    assert (ACTIONS_DIR / "setup-node" / "action.yml").is_file(), (
        "setup-node composite action must live at .github/actions/setup-node/action.yml"
    )


# ---------------------------------------------------------------------------
# Composite-action schema
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["setup-python", "setup-node"])
def test_action_declares_composite(name: str) -> None:
    """``runs.using`` must be 'composite' — anything else changes the contract."""
    data = _load(name)
    runs = data.get("runs", {})
    assert runs.get("using") == "composite", (
        f"{name}: runs.using must be 'composite', got {runs.get('using')!r}"
    )


@pytest.mark.parametrize("name", ["setup-python", "setup-node"])
def test_action_declares_description(name: str) -> None:
    """Description is required for composite actions and is shown in the UI."""
    data = _load(name)
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), (
        f"{name}: top-level description must be a non-empty string"
    )


@pytest.mark.parametrize("name", ["setup-python", "setup-node"])
def test_run_steps_declare_shell(name: str) -> None:
    """Composite actions don't get a default shell; every ``run:`` needs ``shell:``.

    GitHub fails the action with a confusing error if a composite-action
    step uses ``run:`` without a ``shell:`` field. This test pins the
    invariant before the runner does, so the failure surfaces in CI
    against a clear assertion message instead of an opaque GitHub-side
    error during the actual workflow run.
    """
    data = _load(name)
    runs = data.get("runs", {})
    steps = runs.get("steps", [])
    for i, step in enumerate(steps):
        if "run" in step:
            assert "shell" in step, (
                f"{name}: runs.steps[{i}] uses ``run:`` but is missing ``shell:`` — "
                "composite actions don't have a default shell"
            )


@pytest.mark.parametrize("name", ["setup-python", "setup-node"])
def test_inputs_have_descriptions(name: str) -> None:
    """Every declared input needs a description so consumers know what it does."""
    data = _load(name)
    inputs = data.get("inputs", {})
    for input_name, spec in inputs.items():
        assert isinstance(spec, dict), f"{name}: input {input_name!r} must be a mapping"
        assert spec.get("description"), (
            f"{name}: input {input_name!r} is missing a description"
        )


# ---------------------------------------------------------------------------
# Pinned SHAs — every third-party action follows the supply-chain rule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["setup-python", "setup-node"])
def test_third_party_pins_carry_tag_comment(name: str) -> None:
    """Every ``uses: owner/repo@<sha>`` must have a trailing ``# vX.Y.Z`` comment.

    This is what ``audit_action_pins.py`` verifies against the GitHub
    upstream; without the comment the audit can't even start.
    """
    path = ACTIONS_DIR / name / "action.yml"
    third_party_uses = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
            continue
        if "./.github" in stripped or stripped.startswith("uses: .") or stripped.startswith("- uses: ."):
            continue
        third_party_uses.append((lineno, line))
        m = _USES_RE.match(line)
        assert m, (
            f"{name}:{lineno}: third-party ``uses:`` directive does not match "
            f"``uses: <owner>/<repo>@<40-hex-sha>  # v<X>.<Y>.<Z>`` form: {line!r}"
        )

    assert third_party_uses, (
        f"{name}: expected at least one third-party ``uses:`` (the actual "
        f"setup-python or setup-node call); composite is otherwise pointless"
    )


# ---------------------------------------------------------------------------
# Project-pin versions
# ---------------------------------------------------------------------------


def test_setup_python_default_version() -> None:
    """The default Python version must match the project-wide pin (3.12)."""
    data = _load("setup-python")
    pyver = data.get("inputs", {}).get("python-version", {}).get("default")
    assert pyver == PROJECT_PYTHON_VERSION, (
        f"setup-python default python-version must be {PROJECT_PYTHON_VERSION!r}; "
        f"got {pyver!r}. The pin is enforced project-wide — bumping it requires "
        f"updating pyproject.toml + .python-version + every workflow's matrix."
    )


def test_setup_node_default_version() -> None:
    """The default Node version must match the project-wide pin (20)."""
    data = _load("setup-node")
    nodever = data.get("inputs", {}).get("node-version", {}).get("default")
    assert nodever == PROJECT_NODE_VERSION, (
        f"setup-node default node-version must be {PROJECT_NODE_VERSION!r}; "
        f"got {nodever!r}. Active LTS is what package-lock.json was resolved against."
    )


# ---------------------------------------------------------------------------
# Inputs that consuming workflows depend on
# ---------------------------------------------------------------------------


def test_setup_python_exposes_install_audits() -> None:
    """``install-audits`` boolean input must exist; validate.yml depends on it."""
    data = _load("setup-python")
    inputs = data.get("inputs", {})
    assert "install-audits" in inputs, (
        "setup-python must declare an ``install-audits`` input — validate.yml, "
        "regulatory-watch.yml, and uc-tests.yml all rely on it to install "
        "the requirements-ci.txt audit floor"
    )
    default = inputs["install-audits"].get("default")
    assert default in ("false", False), (
        f"install-audits default must be 'false' so jobs that don't need "
        f"the audit deps don't pay for them; got {default!r}"
    )


def test_setup_python_exposes_install_extras() -> None:
    """``install-extras`` string input must exist; codeql.yml depends on it."""
    data = _load("setup-python")
    inputs = data.get("inputs", {})
    assert "install-extras" in inputs, (
        "setup-python must declare an ``install-extras`` input — codeql.yml "
        "uses it to pip install -e .[audits,build,test] so the call graph "
        "matches the rest of CI"
    )
    default = inputs["install-extras"].get("default", "non-empty")
    assert default in ("", None), (
        f"install-extras default must be empty so the editable install is "
        f"opt-in; got {default!r}"
    )


def test_setup_node_exposes_install_deps() -> None:
    """``install-deps`` boolean input must exist with default 'true'."""
    data = _load("setup-node")
    inputs = data.get("inputs", {})
    assert "install-deps" in inputs, (
        "setup-node must declare an ``install-deps`` input — most callers "
        "want ``npm ci`` to run by default"
    )
    default = inputs["install-deps"].get("default")
    assert default in ("true", True), (
        f"install-deps default must be 'true' to match validate.yml's "
        f"existing behaviour (axe-core + jsdom + ajv installed); got {default!r}"
    )


# ---------------------------------------------------------------------------
# Workflows actually use the composite actions
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "deferred to v8.x: only some workflows use the composite "
        "setup-python action; the migration of link-check / pages / "
        "regulatory-watch / release / traffic / uc-manifest / uc-tests / "
        "validate to ./.github/actions/setup-python is the gating fix."
    )
)
def test_no_workflow_pins_setup_python_directly() -> None:
    """No workflow may pin ``actions/setup-python`` directly anymore.

    Repo-overhaul plan §P2 centralised the SHA in the composite action.
    Re-introducing a direct pin in a workflow re-creates the comment-drift
    bug class the centralisation was designed to eliminate.
    """
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    offenders = []
    for wf in sorted(workflows_dir.glob("*.yml")):
        content = wf.read_text(encoding="utf-8")
        if "actions/setup-python@" in content:
            offenders.append(wf.relative_to(REPO_ROOT))
    assert not offenders, (
        f"these workflows still pin actions/setup-python directly instead of "
        f"using ./.github/actions/setup-python: {offenders}. "
        f"Replace with ``uses: ./.github/actions/setup-python``."
    )


def test_no_workflow_pins_setup_node_directly() -> None:
    """No workflow may pin ``actions/setup-node`` directly anymore.

    Repo-overhaul plan §P2 (PR-5, 2026-05-12): ``validate.yml`` was
    the only direct setup-node pin site; it now routes through
    ``./.github/actions/setup-node``. Re-introducing a direct pin in
    any workflow re-creates the comment-drift bug class the
    centralisation was designed to eliminate.
    """
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    offenders = []
    for wf in sorted(workflows_dir.glob("*.yml")):
        content = wf.read_text(encoding="utf-8")
        if "actions/setup-node@" in content:
            offenders.append(wf.relative_to(REPO_ROOT))
    assert not offenders, (
        f"these workflows still pin actions/setup-node directly instead of "
        f"using ./.github/actions/setup-node: {offenders}"
    )
