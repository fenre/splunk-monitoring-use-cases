# `uc.schema.json` changelog

Per-schema lifecycle log. Contract: see [`docs/schema-versioning.md`](../../docs/schema-versioning.md).

| Version | Released  | Stability | Notes                                                                                                  |
|---------|-----------|-----------|--------------------------------------------------------------------------------------------------------|
| 1.5.0   | 2026-Q2   | stable    | Added one optional field, `grandmaExplanation` — a 1–3 sentence plain, jargon-free 'explain it to my grandma' summary of the use case. No Splunk / SPL / CIM / MITRE / TA / acronyms; uses 'we' voice. Rendered as the primary UC text across every surface of the non-technical view (detail panel, UC cards, search results, subcategory lists, recently-added, and area lists inside category views). Generator-owned: populated by `scripts/generate_grandma_explanations.py` from the existing `title`, `description`, `value`, `implementation`, and `monitoringType` fields; gated in CI via a `--check` drift guard that fails PRs adding a UC without running the generator. `maxLength: 400` so card and panel layouts do not overflow. Additive and optional — every previously-valid UC remains valid. |
| 1.4.0   | 2026-Q2   | stable    | Added two optional fields to model curator-defined implementation ordering (the "crawl → walk → run" roadmap): `wave` (enum `crawl` / `walk` / `run`, a per-UC maturity tier within its category) and `prerequisiteUseCases` (array of `UC-X.Y.Z` ids that must be implemented before this UC produces value). Both are optional and additive — every previously-valid UC remains valid. The build (`build.py`) validates `prerequisiteUseCases` against the full catalogue: unknown ids, self-references, and cycles (Kahn's topological sort) fail the build; a crawl UC whose prereqs include a walk/run UC prints a wave-monotonicity warning. A new top-level `implementationRoadmap` object in `catalog.json` groups each category's UCs into crawl/walk/run/unassigned buckets for UI rendering. Consumers on the v1 API (`/api/v1/compliance/ucs/{uc}.json`, `/api/v1/recommender/uc-thin.json`) now surface both fields. The `wave` enum uses `crawl` / `walk` / `run` rather than `foundation` / `intermediate` / `advanced` specifically to avoid value collision with the `difficulty` enum (which already defines `advanced`). |
| 1.3.0   | 2026-Q2   | stable    | Added three optional fields to round-trip metadata that the v6 markdown parser produced but the v1.2 schema dropped on the floor: `subcategory` (explicit subcategory bucket override; needed when a UC is intentionally cross-listed under a subcategory whose number does not match the id prefix — e.g. UC-4.4.32 lives under 4.5 'Serverless & FaaS' — and now also accepts a `<id>#<n>` disambiguator so legacy markdown that placed UCs under two sections sharing the same number, like `### 22.3 DORA` vs `### 22.3 — DORA (extended clauses)`, can round-trip without inventing new public ids); `hardware` (verbatim '- **Hardware:**' markdown line, used by hardware-specific UCs like BMC sensors); `telcoUseCase` (verbatim '- **Telco Use Case:**' line, used by cat-21 industry-vertical UCs). All three are optional and additive — every previously-valid UC remains valid. The new content-tree loader (`tools/build/parse_content.py`) reads them when present and falls back to the legacy id-prefix / TA-string derivations when absent. |
| 1.2.0   | 2026-Q2   | stable    | Documentation correction: `compliance` is no longer in `required`; it stays `minItems: 1` when present. The original v1 design assumed every UC would carry a clause mapping, but the actual corpus is ~78 % operational/observability UCs with no intrinsic compliance hook (the v6 build never validated against this schema, so the constraint was aspirational). Also extended the `monitoringType` enum with `Analytics`, `Anomaly`, `Business`, `Configuration`, `Fault`, `Fraud`, `Inventory`, `Patient Safety`, `Reliability`, `Revenue Assurance`, and `Trading` to cover the values curators have been using in practice. Added `soc_operations` to `securityDomain`. Relaxed `detectionType` from a 5-value enum to a free-form string with a description that explains both taxonomies that coexist in the corpus (SOC detection categories vs. IOC / risk-object entity types). Extended `premiumApps` enum with `Splunk Edge Hub`, `Splunk OT Security Add-on`, `Splunk OT Intelligence`, `Splunk App for Fraud Analytics`, and `Splunk Airport Ground Operations App`. Backward-compatible: every previously-valid UC remains valid; only previously-invalid UCs (in the corpus) now validate. |
| 1.1.0   | 2025-Q4   | stable    | Added `compliance[].priorityWeight` (numeric 0.2/0.4/0.7/1.0) and `compliance[].sourceTags[]`. Backwards compatible — both fields are optional and default to `null`. |
| 1.0.0   | 2025-Q3   | stable    | Initial release. Locked at Phase 1.1. Required fields: `id`, `title`, `compliance`. JSON-first authoring schema for Splunk Monitoring Use Cases. |

## Stability commitment

`x-stability: stable` — no breaking changes will be made within the v1 major.
Additive (minor) changes are allowed; all consumers MUST tolerate unknown
fields per the [tolerant-consumer rule](../../docs/api-versioning.md#tolerant-consumer-rule).

## Migration plan

A v2 major will be branched only when a breaking change is unavoidable
(e.g. renaming a field, tightening an enum, or making a previously-optional
field required). When that happens:

1. The new schema lives at `/schemas/v2/uc.schema.json`.
2. v1 stays online for ≥12 months at `/schemas/v1/uc.schema.json`.
3. A migration tool ships under `tools/build/migrate_v1_to_v2.py`.
4. A migration guide ships at `docs/migrations/uc-v1-to-v2.md`.

Loosening a constraint (the v1.2.0 change above) is additive and stays in v1
because no previously-valid UC becomes invalid.
