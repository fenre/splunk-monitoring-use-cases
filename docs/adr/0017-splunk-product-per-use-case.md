# ADR-0017: Splunk product per use case

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Repository maintainers
- **Builds on:** [ADR-0016](0016-permanent-uc-identifiers.md) (identity fingerprint), [ADR-0015](0015-cost-field-group.md) (optional field-group checklist)

## Context

Every use case in the catalogue is modelled as an SPL search on the Splunk
platform: `spl` is a required field, the gold tier requires it, the build
generates "Run the SPL query" guidance when no implementation guide exists,
and the recommender app falls back to `index=* earliest=-15m` when `spl` is
empty.

Some outcomes are not implemented in SPL at all. A SignalFlow detector lives in
Splunk Observability Cloud; an evaluator or Agent Control rule lives in Splunk
Agent Observability; a playbook lives in Splunk SOAR; a protocol source lives on
Splunk Edge Hub. Use cases for those products today either cannot be authored,
or they carry SPL that reports on a mirror of the product instead of
implementing the outcome (for example `| makeresults` checklists, or searches
over sourcetypes with no documented ingest path).

`premiumApps` records licensing and dependencies. It does not say where the use
case is implemented.

## Decision

Add two optional fields at schema version **1.9.0**:

- **`products[]`** — ordered product ids. The first is where the use case is
  implemented; later ones are where it is also used. Omitted means
  `["splunk-platform"]`. "Splunk platform" is Splunk's term for Splunk
  Enterprise and Splunk Cloud Platform, where SPL runs.
- **`productArtifacts[]`** — `{product, type, language, title, body, docsUrl?}`
  for non-SPL implementation artifacts. `type` uses each product's own object
  names (`detector`, `evaluator`, `stream-alert`, `agent-control`, `playbook`,
  `service`, `kpi`, `aggregation-policy`, `source-configuration`).

SPL stays in `spl`; the locked `catalog.json` key `q` is unchanged. In
`catalog.json` the new fields are `prd` and `pra`, emitted only when the value
is not the default.

Product behaviour lives in one registry,
[`data/splunk-products.json`](../../data/splunk-products.json) (schema
[`schemas/splunk-products.schema.json`](../../schemas/splunk-products.schema.json)),
read only through `splunk_uc.products`. Each row holds:

| Attribute | Used by |
|---|---|
| `id`, `name`, `shortName`, `docsUrl` | UC pages, SPA badge, MCP payload |
| `requires` | `audit-uc-structure` and gold tiers (fields the primary product makes mandatory) |
| `audits` | Lift-loop SPL-token and sourcetype checks |
| `exports` (`savedSearches`, `dashboards`) | Recommender app saved searches, alert-action templates, dashboard generator |
| `fingerprintFields` | `data/id-ledger.json` content fingerprint |
| `qualityProfile.implementSection` | Gold step-2 heading (e.g. "Create the search and alert" vs "Create the detector") |
| `artifactTypes` | Allowed `productArtifacts[].type` values |

**No consumer branches on a product id.** A test fails on a hard-coded product
id in consumer code outside `splunk_uc.products`.

**Identity.** For `splunk-platform` the fingerprint stays `title + spl`, so the
ledger is byte-identical. Each fingerprint revision records the
`fingerprintFields` it was hashed from, so a later product change does not make
old hashes unverifiable. Moving a use case to another product keeps its
identifier (same intent) and appends a fingerprint revision, recorded in a
`bulk_fingerprint_change` manifest under `data/uc-id-migrations/`.

## Consequences

**Positive:** Use cases for Splunk Observability Cloud, Splunk Agent
Observability, Splunk SOAR, Splunk ITSI, and Splunk Edge Hub can carry their
real artifacts instead of fake SPL. Non-SPL use cases are no longer counted as
tier "none", never receive generated SPL instructions, and never ship as saved
searches or dashboards.

**Negative:** A second place to look for implementation content. Adding a
product means a registry row plus a schema enum entry; a test keeps the two in
lockstep.

## Checklist (following ADR-0015)

- Schema: [`schemas/uc.schema.json`](../../schemas/uc.schema.json) 1.9.0, changelog [`schemas/changelogs/uc.md`](../../schemas/changelogs/uc.md)
- Types: [`tools/build/models.py`](../../tools/build/models.py), [`src/splunk_uc/models/use_case.py`](../../src/splunk_uc/models/use_case.py)
- Registry accessor: [`src/splunk_uc/products.py`](../../src/splunk_uc/products.py)
- Field reference: [`docs/use-case-fields.md`](../use-case-fields.md), [`docs/catalog-schema.md`](../catalog-schema.md)

## Alternatives considered

- **Fold `products` into `premiumApps`** — rejected; `premiumApps` is a
  licensing signal and many platform use cases list a premium app they run on.
- **Extend `data/equipment-app-map.json`** — rejected; it maps equipment slugs
  to Splunkbase apps for the picker, not use cases to products.
- **Branch on product id in each consumer** — rejected; every new product would
  touch every consumer.
- **Put non-SPL artifacts in `spl`** — rejected; it breaks every SPL audit and
  the `q` contract.

## Links

- Registry: [`data/splunk-products.json`](../../data/splunk-products.json)
- Ledger: [ADR-0016](0016-permanent-uc-identifiers.md), [`data/id-ledger.json`](../../data/id-ledger.json)
