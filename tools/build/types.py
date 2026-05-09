"""Typed data models for the SSOT — UC sidecars, catalog wire format, regulations.

Repo-overhaul plan §P4 step 2 (2026-05-08): introduces structural types
for the three canonical data shapes in the catalogue so that build,
audit, and MCP code can move from ``dict[str, Any]`` accesses to typed
field accesses without a runtime cost.

Design constraints
------------------

ADR-0004 mandates stdlib-only for the build pipeline and audits. This
module therefore uses ``typing.TypedDict`` and ``typing.Literal`` rather
than pydantic / attrs / dataclasses-json. ``TypedDict`` is purely a
static-typing construct: at runtime, instances are plain ``dict`` values
indistinguishable from JSON-loaded payloads. That gives us:

  1. **Zero runtime cost.** No instantiation, no validation overhead,
     no copies. Existing code that returns ``dict`` from
     ``json.load(...)`` already conforms to the type.
  2. **Mypy-checkable field access.** ``uc["title"]`` is type-checked
     against the TypedDict; missing or misspelled keys are flagged
     statically.
  3. **Schema parity.** Field names mirror ``schemas/uc.schema.json``
     (full-name shape) and ``docs/catalog-schema.md`` (abbreviated
     wire shape). The drift gate ``test_types_match_schema`` keeps
     them in lockstep.

What's modelled
---------------

* :class:`UseCase` — the JSON sidecar shape under ``content/cat-NN-<slug>/UC-X.Y.Z.json``.
  Mirrors ``schemas/uc.schema.json`` v1.7.0.
* :class:`CatalogUC` — the abbreviated UC payload that lives inside
  ``catalog.json`` (and ``data.js`` / ``api/cat-N.json``). Field name
  abbreviations are documented in ``docs/catalog-schema.md``.
* :class:`CatalogJson` — top-level ``catalog.json`` shape: ``DATA``,
  ``CAT_META``, ``CAT_GROUPS``, ``EQUIPMENT``, …
  Distinct from ``parse_content.Catalog`` (the in-memory dataclass that
  the build pipeline passes between stages); :class:`CatalogJson`
  describes the on-disk wire format that ``render_legacy_artifacts``
  emits.
* :class:`RegulationFramework` — one entry from
  ``data/regulations.json``'s ``frameworks`` array.
* :class:`ComplianceMapping` — one entry from a UC's ``compliance``
  array, used by the cat-22 evidence packs and clause coverage report.

What's NOT modelled (yet)
-------------------------

* Per-stage build-pipeline intermediates (e.g. the enrichment cache
  dictionaries). Those are private to ``tools/build/enrichment.py``
  and don't cross module boundaries, so the typing payoff is low.
* MCP wire types. Those live in ``mcp/src/splunk_uc_mcp/tools/`` and
  are governed by their own JSON Schemas; reusing the catalog types
  there is a P9 migration task.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict


# ---------------------------------------------------------------------------
# Primitive type aliases — make the field shapes self-documenting.
# ---------------------------------------------------------------------------

#: Use-case id without the ``UC-`` prefix, e.g. ``"22.35.1"``.
#: Format: ``<category>.<subcategory>.<index>``, all integers.
UCId = str

#: Use-case id with the ``UC-`` prefix, e.g. ``"UC-22.35.1"``.
#: Used by ``prerequisiteUseCases`` and external references.
FullUCId = str

#: Subcategory key, e.g. ``"22.35"`` or ``"22.3#1"`` (disambiguator form
#: for cat-22 cross-cutting families). See uc.schema.json#subcategory.
SubcategoryKey = str

#: Regulation framework identifier from data/regulations.json#frameworks[].id,
#: e.g. ``"gdpr"``, ``"pci-dss"``, ``"nist-800-53"``.
RegulationId = str

#: Regulation version string, e.g. ``"2016/679"`` (GDPR), ``"v4.0"`` (PCI DSS).
RegulationVersion = str

#: Clause id as written in the authoritative regulation, e.g.
#: ``"Art.32(1)(b)"`` (GDPR), ``"§164.312(b)"`` (HIPAA).
ClauseId = str

#: Splunkbase numeric app id, e.g. ``5631`` for Splunk_TA_cisco_meraki.
SplunkbaseAppId = int

#: Splunk pillar (top-level product family).
SplunkPillar = Literal["Security", "Observability", "Platform", "IT Operations"]

#: Implementation maturity tier (the crawl → walk → run roadmap).
WaveTier = Literal["crawl", "walk", "run"]

#: Risk / business impact rating.
Criticality = Literal["critical", "high", "medium", "low"]

#: Implementation difficulty rating.
Difficulty = Literal["beginner", "intermediate", "advanced", "expert"]

#: Compliance assurance level. Weights: full=1.0, partial=0.5, contributing=0.25.
Assurance = Literal["full", "partial", "contributing"]

#: Compliance mode: how the UC relates to the clause it claims.
ComplianceMode = Literal["satisfies", "detects-violation-of"]

#: Provenance source for a compliance mapping.
ComplianceProvenance = Literal[
    "maintainer",
    "auditor-reviewed",
    "olir-crosswalk",
    "nist-cprt-ingest",
    "derived-from-parent",
]


# ---------------------------------------------------------------------------
# UseCase sidecar — full-name shape (content/cat-NN-<slug>/UC-X.Y.Z.json).
# ---------------------------------------------------------------------------


class EvidenceSigning(TypedDict, total=False):
    """How evidence produced by this UC is timestamped or signed."""

    method: Literal["rfc3161-tsa", "sigstore", "gpg", "none"]
    tsaUrl: str
    signer: str


class DerivationSource(TypedDict, total=False):
    """Provenance metadata when a compliance entry was derived from a parent regulation."""

    parentRegulation: RegulationId
    parentVersion: RegulationVersion
    parentClause: ClauseId
    parentAssurance: Assurance
    inheritanceMode: Literal["identity", "mapped"]
    divergenceNote: str


class ComplianceMapping(TypedDict, total=False):
    """One entry in a UC's ``compliance`` array.

    Schema source of truth: ``schemas/uc.schema.json`` ``compliance.items``
    (v1.7.0). Required keys (``regulation``, ``version``, ``clause``,
    ``mode``, ``assurance``, ``assurance_rationale``) are not enforced
    by ``TypedDict`` — runtime validation lives in
    ``scripts/audit_compliance_mappings.py``.
    """

    regulation: RegulationId
    version: RegulationVersion
    clause: ClauseId
    clauseUrl: str
    mode: ComplianceMode
    assurance: Assurance
    assurance_rationale: str
    controlObjective: str
    evidenceArtifact: str
    obligationRef: str
    requires_sme_review: bool
    provenance: ComplianceProvenance
    signedBy: str
    derivationSource: DerivationSource
    legalCaveat: str
    smeCaveat: str


class ControlTest(TypedDict, total=False):
    """Control-test definition: positive and negative scenarios."""

    positiveScenario: str
    negativeScenario: str
    fixtureRef: str
    attackTechnique: str
    fixtureStatus: Literal["pending", "draft", "approved"]


class SplunkbaseAppEntry(TypedDict, total=False):
    """One entry in a UC's ``splunkbaseApps`` array (schema v1.7.0)."""

    id: SplunkbaseAppId
    name: str
    url: str
    minVersion: str
    role: Literal["primary", "data-source", "premium", "optional"]
    setupSkill: str
    requiresSmeReview: bool


class PremiumAppEntry(TypedDict, total=False):
    """One entry in a UC's ``premiumApps`` array.

    The schema accepts both a bare string and an object form. We model
    only the object form here; string entries are also valid at the
    JSON layer (use ``str | PremiumAppEntry`` in field annotations).
    """

    name: str
    displayName: str
    note: str


class UseCaseReference(TypedDict, total=False):
    """One entry in a UC's ``references`` array (schema v1.6+)."""

    title: str
    url: str
    sourceType: str


class TaLinkEntry(TypedDict, total=False):
    """Wire-format shape of ``CatalogUC.ta_link``.

    Emitted by ``tools/build/enrichment.py:ta_link_for_ta_string()`` when
    a TA / Splunkbase reference resolves to the live registry. The
    consumer pages it via ``ta["name"]``, ``ta["url"]`` and (rarely)
    ``ta["id"]`` for the Splunkbase numeric ID.

    Pre-2026-05-09 this field was annotated as a bare ``str`` in
    ``CatalogUC``; that was incorrect — the live runtime shape has
    always been a dict. Fixing the annotation here is the P4 step 3
    consumer-migration audit catching a real type-bug, not a runtime
    behaviour change.
    """

    name: str
    url: str
    id: int


class UseCase(TypedDict, total=False):
    """JSON sidecar shape for ``content/cat-NN-<slug>/UC-X.Y.Z.json``.

    The schema-required fields are ``id`` and ``title``. ``TypedDict``'s
    ``total=False`` makes everything structurally optional; runtime
    validation against ``schemas/uc.schema.json`` lives in
    ``scripts/audit_uc_structure.py``.

    Field names mirror ``schemas/uc.schema.json`` 1:1 — including the
    ``$schema`` key (which is a TypedDict alias because ``$`` is not a
    legal Python identifier).
    """

    # Required by uc.schema.json — but TypedDict can't express both
    # total=False AND required keys without a base class trick. We
    # accept the looseness here because audit_uc_structure.py is the
    # runtime gate.
    id: UCId
    title: str

    # Optional structural / classification fields.
    subcategory: SubcategoryKey
    criticality: Criticality
    difficulty: Difficulty
    wave: WaveTier
    prerequisiteUseCases: list[FullUCId]
    monitoringType: list[str]
    splunkPillar: SplunkPillar
    industry: str

    # Compliance / governance.
    owner: str
    controlFamily: str
    exclusions: str
    evidence: str
    evidenceSigning: EvidenceSigning
    compliance: list[ComplianceMapping]
    controlTest: ControlTest

    # Data sources / SPL.
    dataSources: str
    app: str
    splunkbaseApps: list[SplunkbaseAppEntry]
    premiumApps: list[str | PremiumAppEntry]
    spl: str
    cimSpl: str
    cimModels: list[str]
    schema: str
    dataModelAcceleration: str

    # Narrative / docs.
    description: str
    value: str
    grandmaExplanation: str
    implementation: str
    detailedImplementation: str
    scriptExample: str
    visualization: str

    # Equipment / hardware.
    equipment: list[str]
    equipmentModels: list[str]
    hardware: str

    # Operational metadata.
    references: list[UseCaseReference]
    requiredFields: list[str]
    knownFalsePositives: str
    lastReviewed: str
    reviewer: str
    status: str
    splunkVersions: list[str]
    detectionType: str
    securityDomain: str
    dataDomain: list[str]
    mitreAttack: list[str]
    telcoUseCase: str


# ---------------------------------------------------------------------------
# Catalog wire format (abbreviated keys) — catalog.json + api/cat-N.json + data.js.
# ---------------------------------------------------------------------------


class CatalogUC(TypedDict, total=False):
    """A UC entry inside ``catalog.json#DATA[].s[].u[]`` (abbreviated keys).

    Field abbreviation map: ``docs/catalog-schema.md``. The abbreviated
    keys are used so the 80 MB ``catalog.json`` shrinks by ~25% over
    the full-name form. SSOT field semantics are inherited from
    :class:`UseCase`; the build emits ``i = uc.id``, ``n = uc.title``,
    ``c = uc.criticality``, etc.

    Field-name mapping vs :class:`UseCase`:

    ============== ====================== =========================================
    Wire key       UseCase source field   Notes
    ============== ====================== =========================================
    ``ind``        ``industry``           Cat-22 industry tag
    ``tuc``        ``telcoUseCase``       Telco-specific use case classifier
    ``pillar``     ``splunkPillar``       Computed if absent (security/obs/both)
    ``regs``       compliance[].regulation Set of unique regulation ids
    ``cmp``        compliance[]          Per-clause assurance summary
    ``escu``       (computed)            True when app field includes ESCU/ES
    ``escu_rba``   (computed)            True for risk-based-alerting ESCU UCs
    ``_qs``        (computed)            Quality-score depth indicator (internal)
    ``_qt``        (computed)            Quality-tier label (internal)
    ============== ====================== =========================================
    """

    # Identity / classification.
    i: UCId
    n: str
    c: Criticality
    f: Difficulty
    wv: WaveTier
    pre: list[FullUCId]

    # Narrative.
    v: str
    ge: str

    # Apps / data.
    t: str
    d: str
    sapp: list[SplunkbaseAppEntry]
    ta_link: TaLinkEntry
    premium: list[str | PremiumAppEntry]

    # SPL.
    q: str
    qs: str
    a: list[str]
    schema: str
    dma: str

    # Implementation.
    m: str
    md: str
    z: str
    script: str

    # Operational metadata.
    mtype: list[str]
    kfp: str
    refs: str
    mitre: list[str]
    dtype: str
    sdomain: str
    reqf: str

    # Quality / lifecycle.
    status: str
    reviewed: str
    sver: list[str]
    rby: str

    # Equipment.
    e: list[str]
    em: list[str]
    hw: str

    # Cat-22 / pillar / regulation enrichment.
    ind: str
    tuc: str
    pillar: str
    regs: list[RegulationId]
    cmp: list[ComplianceMapping]
    escu: bool
    escu_rba: bool

    # Internal quality scoring (prefixed with `_` so consumers know
    # they're build-internal, not part of the stable wire surface).
    _qs: int
    _qt: str
    _qg: str


class CatalogSubcategory(TypedDict, total=False):
    """One entry in ``catalog.json#DATA[].s[]``.

    ``qa`` and ``qd`` are quality stats emitted by the build:
    ``qa`` = number of UCs at gold/silver tier in the subcategory,
    ``qd`` = total UC count in the subcategory.

    ``g`` is the optional repo-relative path to the integration guide
    (``docs/guides/<slug>.md``) curated for this subcategory. Surfaced
    in the SSOT-derived ``dist/catalog.json`` from the per-subcategory
    ``_category.json`` ``guide`` field; the legacy ``catalog.json`` did
    not carry it.
    """

    i: SubcategoryKey
    n: str
    u: list[CatalogUC]
    qa: int
    qd: int
    g: str


class CatalogCategory(TypedDict, total=False):
    """One entry in ``catalog.json#DATA[]``.

    ``src`` is a hint pointing into the source ``content/cat-NN-<slug>/``
    directory used by the build to resolve repo-relative links.
    """

    i: int
    n: str
    src: str
    s: list[CatalogSubcategory]


class CategoryMeta(TypedDict, total=False):
    """One entry in ``catalog.json#CAT_META``.

    Field names match the wire format (``desc``, ``quick``) — not the
    schema-style long names. See ``docs/catalog-schema.md#cat_meta``.
    """

    icon: str
    desc: str
    quick: str


class EquipmentEntry(TypedDict, total=False):
    """One entry in ``catalog.json#EQUIPMENT`` for the technology filter.

    Drives the "filter by technology" chip cloud in the static UI.
    Field names match the wire format (``label``, ``tas``, ``models``).
    ``models`` enumerates specific hardware variants the catalogue knows
    about (e.g. ``["IR1101", "IR829"]`` under the ``cisco-ie`` family);
    it's omitted when no model-level granularity exists.
    """

    id: str
    label: str
    tas: list[str]
    models: list[str]


class ImplementationRoadmapEntry(TypedDict, total=False):
    """One per-category entry in ``catalog.json#implementationRoadmap``.

    ``unassigned`` is emitted when a UC in the category does not declare
    a ``wave`` so that consumers can surface coverage gaps explicitly
    rather than silently dropping the UC.
    """

    crawl: list[FullUCId]
    walk: list[FullUCId]
    run: list[FullUCId]
    unassigned: list[FullUCId]


class CatalogJson(TypedDict, total=False):
    """On-disk ``catalog.json`` wire format (and same shape consumed by
    ``api/cat-N.json``, ``data.js`` window globals, MiniSearch shards).

    Distinct from ``tools.build.parse_content.Catalog``: the latter is
    the in-memory dataclass the build pipeline passes between stages
    (``categories``, ``cat_meta``, ``equipment`` lists keyed by Python
    field names); this TypedDict describes the JSON file emitted by
    ``render_legacy_artifacts.render`` (uppercase keys ``DATA``,
    ``CAT_META``, ``EQUIPMENT``).

    Self-describing fields (``_schema_url``, ``_field_map`` …) are
    emitted by the build for downstream consumers (LLM agents reading
    ``catalog.json`` get the field-name mapping inline).

    ``lastModified`` and ``version`` are intentionally NOT part of the
    byte-reproducible build subset (see ``test_legacy_artifacts_parity``):
    ``version`` is sourced from ``VERSION``; ``lastModified`` is the
    git HEAD commit timestamp where available, falling back to the
    process clock.
    """

    _schema_url: str
    _agents_url: str
    _agents_examples_url: str
    _ai_policy_url: str
    _readme: str
    _field_map: dict[str, str]
    DATA: list[CatalogCategory]
    CAT_META: dict[str, CategoryMeta]
    CAT_GROUPS: dict[str, list[int]]
    EQUIPMENT: list[EquipmentEntry]
    implementationRoadmap: dict[str, ImplementationRoadmapEntry]
    lastModified: str
    version: str


# ---------------------------------------------------------------------------
# Regulation framework — data/regulations.json#frameworks[].
# ---------------------------------------------------------------------------


class RegulationCommonClause(TypedDict, total=False):
    """One entry in a regulation version's ``commonClauses`` array.

    ``coverageDecision`` is the curator-assigned coverage classification
    used by the cat-22 clause-navigator (``partial`` / ``full`` /
    ``advisory`` / etc.) and ``obligationSource`` is the deep-link to
    the canonical source clause for traceability.
    """

    clause: ClauseId
    topic: str
    priorityWeight: float
    obligationText: str
    obligationSource: str
    coverageDecision: str


class RegulationVersionEntry(TypedDict, total=False):
    """One entry in a regulation's ``versions`` array.

    ``grammarNotes``, ``versionNotes``, and ``pendingChanges`` are
    curator-authored prose used by the regulatory-watch automation and
    by the per-regulation evidence-pack readers. ``obligationModel`` is
    a small dict pinning where the per-regulation source-map,
    coverage-matrix, and methodology docs live; populated for the cat-22
    tier-1 regulations that have a full obligation model (e.g. NIS2,
    DORA, GDPR).
    """

    version: RegulationVersion
    authoritativeUrl: str
    effectiveFrom: str
    sunsetOn: str | None
    clauseGrammar: str
    clauseExamples: list[ClauseId]
    clauseUrlTemplate: str
    commonClauses: list[RegulationCommonClause]
    grammarNotes: str
    versionNotes: str
    pendingChanges: list[Any]
    obligationModel: dict[str, Any]


class RegulationFramework(TypedDict, total=False):
    """One entry in ``data/regulations.json#frameworks``.

    Drives the cat-22 (regulatory compliance) tooling: clause-coverage
    audit, evidence packs, OSCAL export, and the MCP
    ``find_compliance_gap`` tool. ``$comment`` is an authoring marker
    for curator-only notes; the build ignores it.
    """

    id: RegulationId
    name: str
    shortName: str
    tier: Literal[1, 2, 3]
    jurisdiction: list[str]
    tags: list[str]
    aliases: list[str]
    versions: list[RegulationVersionEntry]


# ---------------------------------------------------------------------------
# Schema parity helpers — used by tests/build/test_types_match_schema.py.
# ---------------------------------------------------------------------------


def use_case_typed_keys() -> set[str]:
    """Return the set of TypedDict-declared field names for :class:`UseCase`.

    Used by the schema-parity test to detect drift between the schema
    and the typed model: any field added to ``schemas/uc.schema.json``
    without a matching ``UseCase`` field breaks the test.
    """
    # ``__annotations__`` includes all TypedDict fields regardless of
    # ``total`` — which is exactly what we want here.
    return set(UseCase.__annotations__.keys())


def catalog_uc_typed_keys() -> set[str]:
    """Return the set of TypedDict-declared field names for :class:`CatalogUC`."""
    return set(CatalogUC.__annotations__.keys())


__all__ = [
    # Primitive aliases
    "UCId",
    "FullUCId",
    "SubcategoryKey",
    "RegulationId",
    "RegulationVersion",
    "ClauseId",
    "SplunkbaseAppId",
    "SplunkPillar",
    "WaveTier",
    "Criticality",
    "Difficulty",
    "Assurance",
    "ComplianceMode",
    "ComplianceProvenance",
    # UC sidecar
    "UseCase",
    "ComplianceMapping",
    "ControlTest",
    "EvidenceSigning",
    "DerivationSource",
    "SplunkbaseAppEntry",
    "PremiumAppEntry",
    "UseCaseReference",
    # Catalog wire format
    "CatalogJson",
    "CatalogCategory",
    "CatalogSubcategory",
    "CatalogUC",
    "CategoryMeta",
    "EquipmentEntry",
    "ImplementationRoadmapEntry",
    # Regulations
    "RegulationFramework",
    "RegulationVersionEntry",
    "RegulationCommonClause",
    # Helpers
    "use_case_typed_keys",
    "catalog_uc_typed_keys",
]


# Suppress unused-import linter warnings when this module is imported
# only for its type aliases. ``Any`` and ``Literal`` are re-exported by
# users that build their own TypedDicts on top of these.
_ = Any
