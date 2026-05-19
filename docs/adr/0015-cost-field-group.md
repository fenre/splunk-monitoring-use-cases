# ADR-0015: Add optional per-UC `cost` field group

- **Status:** Accepted
- **Date:** 2026-05-19
- **Deciders:** Repository maintainers
- **Closes:** Lane F Task F-1 (cost schema head, round 2b schema-cycle slot)

## Context

Consumers of this catalogue — the recommender Splunk app, MCP search filters,
and human curators planning rollout — repeatedly ask which use cases drive
the most Splunk licensing cost (ingest volume, search compute, storage
retention). Today that signal is buried in free-text `implementation` prose
and SPL literals. There is no machine-rankable field, so cost-aware sorting
and filtering is impossible.

## Decision

Introduce an optional top-level **`cost`** object on every UC sidecar at
schema version **1.8.0**. All sub-fields are optional; **`cost.tier`**
(`low` / `medium` / `high` / `extreme`) is the primary coverage key.
Companion fields answer concrete consumer questions: worst-case ingest
(`ingest_gb_per_day`), search intensity (`search_load`), DMA eligibility
(`tstats_eligible`), retention posture (`storage_class`, `retention_days`),
provenance (`estimated_by`, `last_estimated`). Per-region pricing, FX rates,
and dollar amounts are explicitly out of scope — they drift with markets and
belong in customer-specific tooling, not the catalogue schema.

Lane N backfills values by hand for v1. CI ships
`python3 -m splunk_uc audit-cost-coverage` at **`--threshold 0`** (warn-only);
the threshold ratchets upward as coverage grows.

## Consequences

**Positive:** Recommender (F-2), MCP filters (F-3/F-10), and stewardship
dashboards gain a stable sort key without a breaking schema change. The
coverage audit emits a deterministic queue for Lane N backfill.

**Negative:** ~7,929 sidecars start with zero `cost` data; maintainers must
populate tiers over time. A new TypedDict field and audit add maintenance
surface.

## Alternatives considered

- **Free-text `costNotes` string** — rejected; not rankable or filterable.
- **Per-region pricing fields** — rejected; volatile, customer-specific, and
  outside catalogue scope.
- **Generator-emitted cost estimates** — rejected for v1; humans sign off on
  licensing impact; advisory generators may come later with `estimated_by:
  ai-advisory`.

## Links

- Schema: [`schemas/uc.schema.json`](../../schemas/uc.schema.json) v1.8.0
- Changelog: [`schemas/changelogs/uc.md`](../../schemas/changelogs/uc.md)
- Audit: [`src/splunk_uc/audits/cost_coverage.py`](../../src/splunk_uc/audits/cost_coverage.py)
- Field reference: [`docs/use-case-fields.md`](../use-case-fields.md)
