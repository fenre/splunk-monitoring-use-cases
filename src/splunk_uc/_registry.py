"""Verb registry for the ``python -m splunk_uc`` dispatcher.

The registry is a single source of truth for which verbs are
available and where their implementations live. Each verb maps to a
callable that:

- Accepts ``argv: list[str] | None`` (defaults to ``sys.argv[1:]``
  when invoked from the dispatcher).
- Returns an ``int`` exit code (0 on success).
- Has a one-line ``help`` string for ``--help`` output.

Adding a verb is a one-liner: register it here and put the
implementation in ``src/splunk_uc/<subpackage>/<module>.py`` with a
``main`` function. The dispatcher resolves the implementation
lazily, so unrelated dependencies are never imported just because a
sibling verb exists.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


# A ``Verb`` is the public contract every registered command honours.
@dataclass(frozen=True)
class Verb:
    """A single CLI verb backed by a Python callable.

    Attributes
    ----------
    name
        The kebab-case verb users type, e.g. ``audit-reproducibility``.
        Kebab-case is the convention because it lines up with how
        existing Makefile targets are named.
    module
        The fully-qualified import path of the implementation module
        relative to ``splunk_uc`` (e.g. ``audits.build_reproducibility``).
        The module MUST expose a ``main(argv: list[str] | None) -> int``
        callable.
    help
        One-line description shown in ``python -m splunk_uc --help``.
        Keep below 80 characters; this is a human-facing summary.
    category
        Subpackage label used to group verbs in ``--help`` output.
        Currently one of ``audits``, ``generators``, ``ingest``,
        ``migrations``, ``feasibility``.
    """

    name: str
    module: str
    help: str
    category: str


# Registry is intentionally a plain dict[str, Verb] — no late-binding
# magic, no plugin discovery. Migrations land one verb at a time;
# growth is linear and predictable.
_REGISTRY: dict[str, Verb] = {}


def register(verb: Verb) -> None:
    """Register a verb. Duplicate names raise ``ValueError``."""
    if verb.name in _REGISTRY:
        raise ValueError(
            f"verb {verb.name!r} is already registered "
            f"(existing module: {_REGISTRY[verb.name].module!r})"
        )
    _REGISTRY[verb.name] = verb


def get(name: str) -> Verb | None:
    """Look up a verb by name. Returns ``None`` if not registered."""
    return _REGISTRY.get(name)


def all_verbs() -> list[Verb]:
    """Return all registered verbs in registration (insertion) order."""
    return list(_REGISTRY.values())


def by_category() -> dict[str, list[Verb]]:
    """Group registered verbs by category. Insertion order preserved."""
    out: dict[str, list[Verb]] = {}
    for verb in _REGISTRY.values():
        out.setdefault(verb.category, []).append(verb)
    return out


def resolve(name: str) -> Callable[[list[str] | None], int] | None:
    """Resolve a verb name to its concrete ``main`` callable.

    Returns ``None`` if the verb is not registered. Imports the
    implementation lazily so unrelated subpackages don't pay the
    import cost of every other verb.
    """
    verb = get(name)
    if verb is None:
        return None
    import importlib

    module = importlib.import_module(f"splunk_uc.{verb.module}")
    main = getattr(module, "main", None)
    if not callable(main):
        raise RuntimeError(
            f"verb {name!r} module {verb.module!r} does not expose a callable main(argv) -> int"
        )
    # ``getattr`` returns Any; cast to the registered protocol so mypy
    # can prove the dispatcher's contract at the call-site.
    return main  # type: ignore[no-any-return]


# -----------------------------------------------------------------------------
# Built-in verb registrations.
#
# Each registration must point at a real module under src/splunk_uc/. As P6
# migrates more scripts, more registrations land here in the same PR as the
# script body's relocation.
# -----------------------------------------------------------------------------
register(
    Verb(
        name="audit-reproducibility",
        module="audits.build_reproducibility",
        help="Run two --reproducible builds and verify byte-identical output.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-roadmap-consistency",
        module="audits.roadmap_consistency",
        help="Lint ROADMAP.md (sections, links, version drift) + emit JSON snapshot.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-license-inventory",
        module="audits.license_inventory",
        help="Verify data/license-inventory.json matches live pyproject + vendored LICENSE files.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-legacy-orphans",
        module="audits.legacy_orphans",
        help="Diagnose UCs in the legacy use-cases/ tree without a JSON SSOT sidecar.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-coverage-budget",
        module="audits.coverage_budget",
        help="Per-file pytest-cov ratchet for tier-1 + tier-2 paths.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-action-pins",
        module="audits.action_pins",
        help="Verify GitHub Actions SHA pins still match their claimed tag.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-uc-structure",
        module="audits.uc_structure",
        help="Validate UC markdown corpus + JSON sidecars for structural correctness.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-dashboard-spl",
        module="audits.dashboard_spl",
        help="Audit Simple XML dashboard SPL queries for token expansion + REST validity.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-cim-spl-alignment",
        module="audits.cim_spl_alignment",
        help="Detect drift between declared CIM Models and the data models invoked in CIM SPL.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-legal-review-signoffs",
        module="audits.legal_review_signoffs",
        help="Validate data/provenance/legal-review-signoffs.json schema + cross-references.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-regulatory-primer",
        module="audits.regulatory_primer",
        help="Lint docs/regulatory-primer.md for shape, anchors, and UC-count consistency.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-mitre-taxonomy",
        module="audits.mitre_taxonomy",
        help="Validate MITRE ATT&CK technique/tactic IDs in UC sidecars.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-placeholders",
        module="audits.placeholders",
        help="Detect placeholder markers and editorial headers leaking into UC content.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-design-doc-freshness",
        module="audits.design_doc_freshness",
        help="Lint docs/DESIGN.md sections + relative links for drift.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-uc-ids",
        module="audits.uc_ids",
        help="Audit UC-* IDs in use-cases/cat-*.md for duplicates, gaps, wrong category, ordering.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-splunkbase-ids",
        module="audits.splunkbase_ids",
        help="Inventory Splunkbase app ID references and surface naming inconsistencies.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-known-fp",
        module="audits.known_fp",
        help="Flag YAML-import artefacts and placeholders in `Known false positives` fields.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-non-technical-sync",
        module="audits.non_technical_sync",
        help="Cross-check non-technical-view.js against use-cases/cat-*.md UC and category coverage.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-monitoring-type",
        module="audits.monitoring_type",
        help="Validate `Monitoring type:` tokens and Security label coverage for ATT&CK-mapped UCs.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-changelog-uc-refs",
        module="audits.changelog_uc_refs",
        help="Validate CHANGELOG.md headers/dates and UC cross-references in use-cases/cat-*.md.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-repo-consistency",
        module="audits.repo_consistency",
        help="Cross-check INDEX.md, CAT_GROUPS, SPLUNK_APPS, and use-cases/cat-*.md for drift.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-catalog-schema",
        module="audits.catalog_schema",
        help="Validate top-level structure and required keys in catalog.json (stdlib only).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-quality-metadata",
        module="audits.quality_metadata",
        help="Audit per-UC quality metadata coverage (status, reviewer, references, kfp).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-spl-duplicates",
        module="audits.spl_duplicates",
        help="Surface near-duplicate SPL queries across use-cases/cat-*.md (informational).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-links",
        module="audits.links",
        help="Manual audit: check http(s) URLs on - **References:** lines in use-cases/cat-*.md.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-regulation-alignment",
        module="audits.regulation_alignment",
        help="Lint compliance[].regulation against data/regulations.json (id, shortName, aliases).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-nis2-no-gap",
        module="audits.nis2_no_gap",
        help="Validate the NIS2 no-gap obligation matrix and per-UC traceability.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-oscal-roundtrip",
        module="audits.oscal_roundtrip",
        help="Validate OSCAL component-definitions against NIST schema + canonical byte equality.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-regulatory-change-watch",
        module="audits.regulatory_change_watch",
        help="Regulatory change-watch audit (check / fetch / freeze) for tier-1 sources.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-compliance-gaps",
        module="audits.compliance_gaps",
        help="Per-regulation clause-level gap analysis (reports/compliance-gaps.json + .md).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-compliance-mappings",
        module="audits.compliance_mappings",
        help="Validate compliance[] mappings, golden tuple gate, three coverage metrics.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-guide-xrefs",
        module="audits.guide_xrefs",
        help="Detect broken cross-product markdown links in docs/guides/*.md.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-doc-counts",
        module="audits.doc_counts",
        help="Cross-check numeric claims (UC counts) in AGENTS.md / docs/ against actual content.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-openapi-drift",
        module="audits.openapi_drift",
        help="Flag dist/api/ paths missing from openapi.yaml / api/v1/openapi.yaml.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-content-quality",
        module="audits.content_quality",
        help="Flag description==value, jargon in grandmaExplanation, broken fixtureRefs.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-baseline-clause-grammar-free",
        module="audits.baseline_clause_grammar_free",
        help="Phase F drift guard: refuse `clause-grammar` fingerprints in audit-baseline.json.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-peer-review-signoffs",
        module="audits.peer_review_signoffs",
        help="Phase 4.5a peer-review gate: schema + semantic invariants for signoff records.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-mcp-tool-schemas",
        module="audits.mcp_tool_schemas",
        help="Drift guard: MCP tool/resource surface vs. api/v1/* + outputSchema runtime probes.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-gold-profile-v2",
        module="audits.gold_profile_v2",
        help="Gold-standard v2 audit: SPL provenance, KFP separators, deterministic suppressions.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-prerequisites",
        module="audits.prerequisites",
        help="Validate UC prerequisite graph (cycles, unknown IDs, wave monotonicity).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-sandbox-validation",
        module="audits.sandbox_validation",
        help="Audit sample-data/ fixture coverage and shape against UCs that declare fixtureRef.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-sme-review-signoffs",
        module="audits.sme_review_signoffs",
        help="Validate data/provenance/sme-signoffs.json schema + cross-references to UC sidecars.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-mapping-ledger",
        module="audits.mapping_ledger",
        help="Validate data/provenance/mapping-ledger.json (schema + hash chain + integrity).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-gold-profile",
        module="audits.gold_profile",
        help="Gold-standard v1 audit: tier classification (bronze/silver/gold) + depth heuristics.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-perf-a11y",
        module="audits.perf_a11y",
        help="Phase 4.5f performance budgets + accessibility (axe-core under jsdom) gate.",
        category="audits",
    )
)
register(
    Verb(
        name="audit-spl-grammar",
        module="audits.spl_grammar",
        help="Catch SPL grammar bugs (stats span, leading pipe, glued indexes, case wildcards).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-spl-hallucinations",
        module="audits.spl_hallucinations",
        help="Detect SPL hallucinations (unknown commands/funcs, bad CIM datasets, malformed tstats).",
        category="audits",
    )
)
register(
    Verb(
        name="audit-splunk-cloud-compat",
        module="audits.splunk_cloud_compat",
        help="Audit SPL + content packs for Splunk Cloud (Victoria/Classic) compatibility.",
        category="audits",
    )
)
