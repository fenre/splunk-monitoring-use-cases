"""Structural invariants for ``.devcontainer/devcontainer.json``.

Repo-overhaul plan §P11 (2026-05-08): the devcontainer is the canonical
zero-friction onboarding path for new contributors. If it silently
drifts (digest dropped, port forward removed, ``postCreateCommand``
mistyped), new contributors hit confusing breakage on their first
interaction with the project. These tests pin the invariants we rely
on so that drift surfaces in CI, not in a contributor's first hour.

What we lock here
-----------------

* The base image is pinned by an OCI image-index digest so reproducibility
  doesn't depend on Microsoft's tag-mutability policy.
* The Python image major-minor matches the rest of the toolchain
  (Python 3.12 — every CI workflow uses ``python-version: "3.12"``).
* The Node feature is pinned to a major version (``20``) matching
  ``actions/setup-node`` in ``validate.yml``.
* The post-create command hands off to ``make devcontainer-init`` so
  bootstrap logic has a single source of truth.
* Port 8000 is forwarded so ``make serve`` works out of the box.
* The container runs as the non-root ``vscode`` user.

These invariants are deliberately strict; intentional changes to any
of them require updating the test in the same PR, which is the right
review-burden trade-off.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEVCONTAINER_JSON = REPO_ROOT / ".devcontainer" / "devcontainer.json"


def _strip_jsonc_comments(src: str) -> str:
    """Best-effort JSONC → JSON cleaner.

    devcontainer.json is JSON-with-Comments (JSONC), the de-facto
    superset that Microsoft tooling supports. The Python stdlib only
    parses pure JSON, so we strip ``//`` line comments and ``/* … */``
    block comments before handing the source to :func:`json.loads`.

    This is a regex strip rather than a real JSONC tokenizer, so the
    rare case of ``//`` *inside* a string literal would mis-strip.
    Acceptable here because no field in the file embeds ``//`` in a
    string value.
    """
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"(?m)^\s*//.*$", "", src)
    src = re.sub(r"(?m)\s+//.*$", "", src)
    src = re.sub(r",(\s*[}\]])", r"\1", src)
    return src


@pytest.fixture(scope="module")
def devcontainer() -> dict:
    """Parse ``.devcontainer/devcontainer.json`` once per test module."""
    raw = DEVCONTAINER_JSON.read_text(encoding="utf-8")
    return json.loads(_strip_jsonc_comments(raw))


def test_devcontainer_file_exists() -> None:
    """The devcontainer file is checked into the repo."""
    assert DEVCONTAINER_JSON.is_file(), (
        f"missing .devcontainer/devcontainer.json — Phase 11 onboarding "
        f"contract relies on this path"
    )


def test_image_pinned_to_oci_digest(devcontainer: dict) -> None:
    """The base image is pinned by SHA256 digest, not just by tag.

    Microsoft can repoint the ``:3.12`` tag at any time; pinning by
    digest makes a re-pull bit-for-bit reproducible and prevents a
    compromised tag from silently rolling out to all contributors.
    """
    image = devcontainer["image"]
    assert image.startswith("mcr.microsoft.com/devcontainers/python:3.12@sha256:"), (
        f"base image {image!r} is not pinned by sha256: digest"
    )
    digest = image.split("@", 1)[1]
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", digest), (
        f"digest {digest!r} is not a valid sha256:<64-hex>"
    )


def test_python_version_matches_ci(devcontainer: dict) -> None:
    """The devcontainer's Python minor must match the CI workflows.

    Mismatch here is a top source of "works locally, fails in CI"
    bug reports; the tests/lint that pass on Python 3.13 may fail on
    3.12 or vice versa. Every workflow under ``.github/workflows/``
    uses ``python-version: "3.12"``; the devcontainer must match.
    """
    image = devcontainer["image"]
    assert ":3.12@" in image, (
        f"devcontainer Python version drifted from CI; image is {image!r}, "
        "expected ':3.12@sha256:...'"
    )


def test_node_feature_version_matches_ci(devcontainer: dict) -> None:
    """The Node feature is pinned to v20 to match ``actions/setup-node`` in CI."""
    features = devcontainer.get("features", {})
    node_keys = [k for k in features if k.startswith("ghcr.io/devcontainers/features/node")]
    assert node_keys, "Node feature is missing — required for ui-smoke + axe tests"
    node_cfg = features[node_keys[0]]
    assert node_cfg.get("version") == "20", (
        f"Node feature version drifted from CI; got {node_cfg.get('version')!r}, "
        "expected '20' (must match validate.yml's actions/setup-node)"
    )


def test_post_create_uses_make_target(devcontainer: dict) -> None:
    """Bootstrap delegates to a single Make target so logic has one home."""
    assert devcontainer.get("postCreateCommand") == "make devcontainer-init", (
        "postCreateCommand drifted — must delegate to `make devcontainer-init` "
        "so bootstrap logic stays in the Makefile, not duplicated in JSON"
    )


def test_port_8000_forwarded(devcontainer: dict) -> None:
    """`make serve` listens on 8000; forwarding must be configured."""
    forwarded = devcontainer.get("forwardPorts", [])
    assert 8000 in forwarded, (
        f"port 8000 not forwarded; got {forwarded!r}. `make serve` will "
        "fail to be reachable from the host"
    )


def test_runs_as_non_root(devcontainer: dict) -> None:
    """The container runs as the unprivileged ``vscode`` user.

    Codeguard supply-chain rule: avoid running developer tooling as
    root inside the container. The Microsoft base image preconfigures
    a ``vscode`` user with sudo for elevation when needed.
    """
    assert devcontainer.get("remoteUser") == "vscode", (
        f"remoteUser must be 'vscode'; got {devcontainer.get('remoteUser')!r}"
    )


def test_make_target_exists() -> None:
    """The Make target referenced by postCreateCommand actually exists.

    Catches the trivial case where someone removes ``devcontainer-init``
    from the Makefile but forgets to update the JSON. Avoids a
    confusing "make: *** No rule to make target 'devcontainer-init'"
    error inside a freshly built container.

    Unskipped 2026-05-13 in the same PR that added the
    ``devcontainer-init`` target. The previous skip reason
    ("deferred to v8.x") is therefore obsolete.
    """
    makefile = (REPO_ROOT / "Makefile").read_text()
    assert re.search(r"^devcontainer-init:", makefile, flags=re.M), (
        "Makefile is missing the devcontainer-init target referenced by "
        ".devcontainer/devcontainer.json's postCreateCommand"
    )

    # The `.PHONY:` declaration spans multiple physical lines via
    # backslash continuations. Join them into one logical line first so
    # the regex below covers every continuation segment.
    phony_lines: list[str] = []
    in_phony = False
    for line in makefile.splitlines():
        if line.startswith(".PHONY:"):
            in_phony = True
        if in_phony:
            phony_lines.append(line.rstrip().rstrip("\\").rstrip())
            if not line.rstrip().endswith("\\"):
                break
    phony_text = " ".join(phony_lines)
    assert re.search(r"\bdevcontainer-init\b", phony_text), (
        "Makefile's .PHONY declaration is missing the devcontainer-init "
        "entry — without it, an accidental file named 'devcontainer-init' "
        "in the repo root would cause make to skip the target. "
        f"Current .PHONY: {phony_text!r}"
    )
