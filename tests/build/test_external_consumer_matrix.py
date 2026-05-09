"""Structural invariants for :file:`docs/external-consumer-matrix.md`.

Repo-overhaul plan ``p11-consumer-matrix``: this matrix is the public
release contract. If a row goes missing — e.g. someone refactors the
matrix and accidentally drops the MCP tool surface — external consumers
lose the documented commitment that protects their integrations. The
test pins the seven mandatory consumer-surface rows and the
cross-document references that make the contract operable.

What we lock here
-----------------

* The matrix exists at the canonical path.
* It enumerates the seven consumer surfaces called out in the plan
  (MCP wire signatures, per-UC SSG URLs, api/v1/ shapes, MiniSearch
  shards, catalog.json shape, .spl filenames, schema files).
* It defines the five stability tiers (locked / additive-only /
  versioned-bundle / advisory / internal-helper).
* It carries a phase-by-phase risk register so PR authors can
  cross-check their reach.
* It carries a "What we explicitly do not promise" section so the
  contract has clear edges.
* api-versioning.md and url-scheme.md (the two locked-contract
  documents the matrix is the index for) cross-link it so a
  downstream consumer reading either one finds the matrix.
* The rollback / capacity / north-star triad references it so
  internal maintainers see it from every operational angle.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

MATRIX_DOC = REPO_ROOT / "docs" / "external-consumer-matrix.md"
API_VERSIONING = REPO_ROOT / "docs" / "api-versioning.md"
URL_SCHEME = REPO_ROOT / "docs" / "url-scheme.md"
ROLLBACK_PLAYBOOK = REPO_ROOT / "docs" / "rollback-playbook.md"
CAPACITY = REPO_ROOT / "docs" / "capacity-and-staffing.md"

REQUIRED_SURFACES: tuple[tuple[str, str], ...] = (
    ("MCP tool names", r"MCP tool names"),
    ("Per-UC SSG URLs", r"Per-UC SSG URLs"),
    ("api/v1/ versioned endpoints", r"`/api/v1/`\s*versioned endpoints"),
    ("MiniSearch shards", r"MiniSearch shards"),
    ("catalog.json shape", r"`catalog\.json`\s*shape"),
    (".spl package filenames", r"`\.spl`\s*package filenames"),
    ("Schema files", r"Schema files"),
)

REQUIRED_TIERS: tuple[str, ...] = (
    "Locked",
    "Additive-only",
    "Versioned bundle",
    "Advisory",
    "Internal helper",
)


@pytest.fixture(scope="module")
def matrix_text() -> str:
    return MATRIX_DOC.read_text(encoding="utf-8")


def test_matrix_doc_exists() -> None:
    assert MATRIX_DOC.is_file(), (
        f"docs/external-consumer-matrix.md must exist at {MATRIX_DOC}; "
        "the matrix is the public release contract that protects "
        "external consumers from silent breakage (cross-cutting policy "
        "'p11-consumer-matrix')."
    )


@pytest.mark.parametrize(
    "label,pattern",
    REQUIRED_SURFACES,
    ids=[label for label, _ in REQUIRED_SURFACES],
)
def test_matrix_enumerates_all_seven_surfaces(
    matrix_text: str, label: str, pattern: str
) -> None:
    assert re.search(pattern, matrix_text), (
        f"external-consumer-matrix.md must include a row for surface "
        f"'{label}' (pattern {pattern!r}). Removing a row deletes the "
        "documented stability commitment for that surface and would "
        "let consumer-impacting changes ship without a deprecation "
        "trail."
    )


@pytest.mark.parametrize("tier", REQUIRED_TIERS, ids=list(REQUIRED_TIERS))
def test_matrix_defines_all_stability_tiers(matrix_text: str, tier: str) -> None:
    """All five tiers must appear in the document — even ones currently
    unused — so a reviewer adding a new surface row finds the right
    classification."""
    assert tier in matrix_text, (
        f"external-consumer-matrix.md must define stability tier "
        f"'{tier}'. The five-tier classification is what disambiguates "
        "a consumer-grade contract from an internal helper; missing a "
        "tier risks misclassification of new surfaces."
    )


def test_matrix_carries_phase_risk_register(matrix_text: str) -> None:
    assert re.search(r"##\s*Phase-by-phase risk register", matrix_text), (
        "external-consumer-matrix.md must carry a 'Phase-by-phase risk "
        "register' section. PR authors invert the matrix to check 'does "
        "my phase touch any consumer surface'; without the inversion the "
        "matrix is half-blind."
    )


def test_matrix_carries_explicit_non_promises(matrix_text: str) -> None:
    """The negative space matters as much as the positive — without it,
    consumers might assume e.g. /api/cat-N.json is locked when it isn't."""
    assert re.search(r"##\s*What we explicitly do not promise", matrix_text), (
        "external-consumer-matrix.md must carry a 'What we explicitly do "
        "not promise' section. Surfaces that look stable but are not "
        "(e.g. /api/cat-N.json, search-shard hash suffixes, llms.txt "
        "ordering) need to be explicitly listed so consumers don't pin "
        "to them."
    )


def test_matrix_carries_signalling_channels(matrix_text: str) -> None:
    assert re.search(r"##\s*Signalling channels", matrix_text), (
        "external-consumer-matrix.md must document the signalling "
        "channels (CHANGELOG.md → migration-status.md → release body → "
        "MCP deprecation flag → api/v1/manifest.json deprecations[]) "
        "so a consumer who watches a sane subset will catch every break."
    )


def test_api_versioning_links_matrix() -> None:
    text = API_VERSIONING.read_text(encoding="utf-8")
    assert "external-consumer-matrix.md" in text, (
        "docs/api-versioning.md must link external-consumer-matrix.md. "
        "api-versioning is the locking doc for /api/v1/; consumers "
        "reading it must be able to find the broader matrix that "
        "covers MCP, schemas, .spl, and SSG URLs in one view."
    )


def test_url_scheme_links_matrix() -> None:
    text = URL_SCHEME.read_text(encoding="utf-8")
    assert "external-consumer-matrix.md" in text, (
        "docs/url-scheme.md must link external-consumer-matrix.md. "
        "url-scheme.md is the locking doc for /uc/, /category/, "
        "/regulation/; readers must be able to find the broader matrix."
    )


def test_rollback_playbook_links_matrix() -> None:
    text = ROLLBACK_PLAYBOOK.read_text(encoding="utf-8")
    assert "external-consumer-matrix.md" in text, (
        "docs/rollback-playbook.md must link external-consumer-matrix.md. "
        "Any rollback must respect the consumer surfaces named in the "
        "matrix; the cross-link is what tells the on-call reviewer where "
        "to look first."
    )


def test_capacity_doc_links_matrix() -> None:
    text = CAPACITY.read_text(encoding="utf-8")
    assert "external-consumer-matrix.md" in text, (
        "docs/capacity-and-staffing.md must link external-consumer-matrix.md. "
        "Reduced and solo operating modes still preserve the consumer-"
        "surface contract; the cross-link is what makes that promise "
        "discoverable."
    )
