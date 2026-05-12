"""Unit tests for ``python3 -m splunk_uc audit-action-pins``.

Repo-overhaul plan §P2.5 (2026-05-08): the action-pin auditor is a
single point of failure for our supply-chain trust chain — if it stops
detecting SHA-vs-comment drift, the security guarantee documented in
``SECURITY.md`` silently breaks.

These tests cover the pure logic (parser + classifier) without the
network. Coverage is the entry-point ``main`` function with
``resolve_tag_sha`` monkeypatched, plus the small ``collect_pins`` and
``to_owner_repo`` helpers. The actual GitHub API contract is checked
end-to-end by the ``audit-action-pins`` Make target and the matching
CI step in ``validate.yml``; a runtime regression there blocks the
merge.

Test surface
------------

* :func:`test_collect_pins_skips_local_actions` — local actions
  (``./.github/actions/...``) are out of scope for the audit.
* :func:`test_collect_pins_groups_duplicate_pins` — the same
  ``(action, tag, sha)`` referenced from multiple workflows is grouped
  into a single API call.
* :func:`test_to_owner_repo_handles_subpath_actions` —
  ``github/codeql-action/init`` and ``github/codeql-action/analyze``
  resolve to the same ``github/codeql-action`` repo.
* :func:`test_main_exit_zero_when_all_match` — happy path: SHAs match,
  exit 0.
* :func:`test_main_exit_one_on_real_mismatch` — definitive drift fails
  the build.
* :func:`test_main_exit_zero_on_transient_only` — pure rate-limit /
  network failures degrade to a soft warning, not a build failure.
* :func:`test_main_exit_one_on_404` — a 404 on the upstream tag is a
  real authoring bug (the ``# vX.Y.Z`` comment names a tag that
  doesn't exist), so it's classified as a hard mismatch.
* :func:`test_collect_pins_walks_composite_actions` — repo-overhaul
  plan §P2 centralised setup-python / setup-node SHAs into
  ``.github/actions/*/action.yml`` composite actions; those pins
  must remain in scope of the audit.
* :func:`test_collect_pins_accepts_github_dir` — passing
  ``.github/`` (rather than ``.github/workflows/``) is the modern
  call signature; both must work.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_action_pins.py"
SRC_DIR = REPO_ROOT / "src"


def _load_audit_module():
    """Import audit_action_pins without executing main().

    P6 (scripts taxonomy, 2026-05-09) relocated the implementation
    to ``src/splunk_uc/audits/action_pins.py`` with a thin shim at
    the original ``python3 -m splunk_uc audit-action-pins`` path. Tests that
    monkeypatch module-level state (``Path``, ``__file__``,
    ``resolve_tag_sha``) MUST reach the implementation module so
    the patches propagate into the function closures — patching
    the shim only mutates its local re-export. The legacy
    spec-loader path is preserved as a deliberate fallback for an
    unpacked sdist that lost the ``src/`` tree.
    """
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    try:
        import splunk_uc.audits.action_pins as impl

        return impl
    except ImportError:
        pass
    spec = importlib.util.spec_from_file_location("audit_action_pins", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_action_pins"] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# collect_pins / to_owner_repo
# ---------------------------------------------------------------------------


def test_collect_pins_skips_local_actions(tmp_path: Path) -> None:
    """``collect_pins`` ignores local actions like ``./.github/actions/foo``.

    Local actions are versioned as part of this repo, so SHA-pinning
    semantics don't apply.
    """
    aap = _load_audit_module()
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()
    (wf_dir / "demo.yml").write_text(
        """\
name: demo
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/actions/local-action
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
"""
    )
    pins = aap.collect_pins(wf_dir)
    assert len(pins) == 1
    (action, tag, sha), occurrences = next(iter(pins.items()))
    assert action == "actions/checkout"
    assert tag == "v4.2.2"
    assert sha == "11bd71901bbe5b1630ceea73d27597364c9af683"
    assert len(occurrences) == 1


def test_collect_pins_groups_duplicate_pins(tmp_path: Path) -> None:
    """The same ``(action, tag, sha)`` in two files is one entry, two locations."""
    aap = _load_audit_module()
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir()
    body = (
        "jobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2\n"
    )
    (wf_dir / "a.yml").write_text("name: a\non: push\n" + body)
    (wf_dir / "b.yml").write_text("name: b\non: push\n" + body)
    pins = aap.collect_pins(wf_dir)
    assert len(pins) == 1
    occurrences = next(iter(pins.values()))
    # Two different files, same line number per file because the body is identical.
    assert len(occurrences) == 2
    files = sorted(p.name for p, _ in occurrences)
    assert files == ["a.yml", "b.yml"]


def test_collect_pins_walks_composite_actions(tmp_path: Path) -> None:
    """Pins in ``.github/actions/*/action.yml`` are discovered alongside workflows.

    Repo-overhaul plan §P2 centralised setup-python (11 sites) and
    setup-node (1 site) into composite actions. If ``collect_pins``
    didn't walk those files, the centralised SHAs would silently
    escape the audit's drift detection — exactly the failure mode the
    auditor exists to prevent.
    """
    aap = _load_audit_module()
    github_dir = tmp_path / ".github"
    wf_dir = github_dir / "workflows"
    actions_dir = github_dir / "actions" / "setup-python"
    wf_dir.mkdir(parents=True)
    actions_dir.mkdir(parents=True)

    (wf_dir / "demo.yml").write_text(
        """\
name: demo
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: ./.github/actions/setup-python
"""
    )
    (actions_dir / "action.yml").write_text(
        """\
name: setup-python
runs:
  using: composite
  steps:
    - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
"""
    )
    pins = aap.collect_pins(github_dir)
    actions = sorted(action for (action, _, _) in pins.keys())
    assert actions == ["actions/checkout", "actions/setup-python"], (
        f"composite-action SHA escaped audit; got {actions}"
    )


def test_collect_pins_accepts_github_dir(tmp_path: Path) -> None:
    """Passing ``.github/`` works the same as ``.github/workflows/``.

    The legacy call signature (``collect_pins(workflow_dir)``) is
    still supported for back-compat, but the modern one
    (``collect_pins(github_dir)``) is what ``main()`` uses since the
    composite-action expansion.
    """
    aap = _load_audit_module()
    github_dir = tmp_path / ".github"
    wf_dir = github_dir / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "demo.yml").write_text(
        """\
name: demo
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
"""
    )
    pins_via_github = aap.collect_pins(github_dir)
    pins_via_workflows = aap.collect_pins(wf_dir)
    assert pins_via_github == pins_via_workflows, (
        "the .github/ and .github/workflows/ entry points must yield identical pins"
    )


def test_to_owner_repo_handles_subpath_actions() -> None:
    """``github/codeql-action/init`` resolves to ``github/codeql-action``."""
    aap = _load_audit_module()
    assert aap.to_owner_repo("actions/checkout") == "actions/checkout"
    assert aap.to_owner_repo("github/codeql-action/init") == "github/codeql-action"
    assert aap.to_owner_repo("github/codeql-action/analyze") == "github/codeql-action"


def test_to_owner_repo_rejects_malformed() -> None:
    """A bare token without a slash is unparseable and raises."""
    aap = _load_audit_module()
    with pytest.raises(ValueError):
        aap.to_owner_repo("nope")


# ---------------------------------------------------------------------------
# main() integration with monkeypatched resolve_tag_sha
# ---------------------------------------------------------------------------


@pytest.fixture
def workflow_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fixture repo with one .github/workflows/demo.yml + 2 pins."""
    repo = tmp_path / "repo"
    wf_dir = repo / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "demo.yml").write_text(
        """\
name: demo
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
"""
    )
    return repo


def test_main_exit_zero_when_all_match(
    workflow_tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Happy path: every SHA matches its claimed tag → exit 0."""
    aap = _load_audit_module()

    def fake_resolve(owner_repo: str, tag: str, headers: dict[str, str]) -> str:
        return {
            ("actions/checkout", "v4.2.2"): "11bd71901bbe5b1630ceea73d27597364c9af683",
            ("actions/setup-python", "v5.6.0"): "a26af69be951a213d495a4c3e4e4022e16d87065",
        }[(owner_repo, tag)]

    monkeypatch.setattr(aap, "resolve_tag_sha", fake_resolve)
    monkeypatch.setattr(aap, "Path", _PathLike(workflow_tree))
    monkeypatch.setattr(
        aap,
        "__file__",
        str(workflow_tree / "src" / "splunk_uc" / "audits" / "action_pins.py"),
    )

    rc = aap.main()
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "All 2 pins verified" in out
    assert "MISMATCHES" not in out


def test_main_exit_one_on_real_mismatch(
    workflow_tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Definitive SHA drift fails the build with exit 1."""
    aap = _load_audit_module()

    def fake_resolve(owner_repo: str, tag: str, headers: dict[str, str]) -> str:
        if owner_repo == "actions/checkout":
            # claimed v4.2.2 but actually points elsewhere
            return "0000000000000000000000000000000000000000"
        return "a26af69be951a213d495a4c3e4e4022e16d87065"

    monkeypatch.setattr(aap, "resolve_tag_sha", fake_resolve)
    monkeypatch.setattr(aap, "Path", _PathLike(workflow_tree))
    monkeypatch.setattr(
        aap,
        "__file__",
        str(workflow_tree / "src" / "splunk_uc" / "audits" / "action_pins.py"),
    )

    rc = aap.main()
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "MISMATCHES" in out
    assert "actions/checkout" in out
    assert "0000000000" in out


def test_main_exit_zero_on_transient_only(
    workflow_tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rate-limit / network errors degrade to a warning, not a failure."""
    aap = _load_audit_module()

    def always_rate_limit(owner_repo: str, tag: str, headers: dict[str, str]) -> str:
        raise aap._TransientError(f"HTTP 403 from {owner_repo}/{tag}")

    monkeypatch.setattr(aap, "resolve_tag_sha", always_rate_limit)
    monkeypatch.setattr(aap, "Path", _PathLike(workflow_tree))
    monkeypatch.setattr(
        aap,
        "__file__",
        str(workflow_tree / "src" / "splunk_uc" / "audits" / "action_pins.py"),
    )

    rc = aap.main()
    out = capsys.readouterr().out
    assert rc == 0, out  # transient errors must not fail the build
    assert "::warning::" in out
    assert "could not be verified" in out
    # Soft skip is the expected outcome.
    assert "MISMATCHES" not in out


def test_main_exit_one_on_404(
    workflow_tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A 404 on the upstream tag is real drift — the comment names a missing tag."""
    aap = _load_audit_module()

    def resolve_or_404(owner_repo: str, tag: str, headers: dict[str, str]) -> str:
        if owner_repo == "actions/checkout":
            raise ValueError(f"upstream tag {tag!r} does not exist on {owner_repo}")
        return "a26af69be951a213d495a4c3e4e4022e16d87065"

    monkeypatch.setattr(aap, "resolve_tag_sha", resolve_or_404)
    monkeypatch.setattr(aap, "Path", _PathLike(workflow_tree))
    monkeypatch.setattr(
        aap,
        "__file__",
        str(workflow_tree / "src" / "splunk_uc" / "audits" / "action_pins.py"),
    )

    rc = aap.main()
    out = capsys.readouterr().out
    assert rc == 1, out
    assert "MISMATCHES" in out
    assert "does not exist" in out


# ---------------------------------------------------------------------------
# Helper: a Path subclass that resolves to the fixture tree.
# ---------------------------------------------------------------------------


class _PathLike:
    """Stand-in for :class:`pathlib.Path` used to redirect the audit module's

    ``Path(__file__).resolve().parents[1] / ".github" / "workflows"`` chain
    onto the ``tmp_path``-based fixture instead of the real repo.
    """

    def __init__(self, repo_root: Path):
        self._repo_root = repo_root

    def __call__(self, *args: object, **kwargs: object) -> Path:
        return _StubPath(self._repo_root, str(args[0]) if args else ".")


class _StubPath:
    """Minimal pathlib-compatible facade that pretends ``__file__`` lives
    inside the fixture repo so ``Path(__file__).resolve().parents[N]``
    yields the fixture root, not the real repo.

    P6 (scripts taxonomy, 2026-05-09) moved the audit body from
    ``python3 -m splunk_uc audit-action-pins`` (depth 1) to
    ``src/splunk_uc/audits/action_pins.py`` (depth 3). The
    implementation now reads ``parents[3]``; the stub exposes all
    four parent levels so the test continues to redirect into the
    synthetic ``workflow_tree``.
    """

    def __init__(self, repo_root: Path, _path: str):
        self._repo_root = repo_root
        self._path = repo_root / "src" / "splunk_uc" / "audits" / "action_pins.py"

    def resolve(self) -> _StubPath:
        return self

    @property
    def parents(self) -> list[Path]:
        # parents[0] = audits/, parents[1] = splunk_uc/,
        # parents[2] = src/, parents[3] = repo root.
        return [
            self._repo_root / "src" / "splunk_uc" / "audits",
            self._repo_root / "src" / "splunk_uc",
            self._repo_root / "src",
            self._repo_root,
        ]
