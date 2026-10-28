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
Splunk Observability Cloud<sup class="ref">[<a href="#ref-5">5</a>]</sup>; an evaluator or Agent Control rule lives in Splunk
Agent Observability; a playbook lives in Splunk SOAR<sup class="ref">[<a href="#ref-6">6</a>]</sup>; a protocol source lives on
Splunk Edge Hub<sup class="ref">[<a href="#ref-3">3</a>]</sup>. Use cases for those products today either cannot be authored,
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

**Finding use cases that fake another product.** `audit-uc-product-fit`
reports a use case when its SPL only hard-codes rows (`| makeresults` with no
data read), when it reads a sourcetype or index that
[`data/product-fit-rules.json`](../../data/product-fit-rules.json) attributes
to another product but that product's documentation does not name as a
default ingest path, or when the SPL reads that product's data while the
implementation prose configures one of its objects. Each rule cites a product
skill or vendor document. Candidates are reviewed into
[`data/product-fit-review.json`](../../data/product-fit-review.json)
(`migrate`, `keep`, or `needs-sme-review`; only reviewed verdicts with evidence
are migrated). The audit is warn-only until the migrations land, then runs
with `--strict`.

## Consequences

**Positive:** Use cases for Splunk Observability Cloud, Splunk Agent
Observability, Splunk SOAR, Splunk ITSI<sup class="ref">[<a href="#ref-4">4</a>]</sup>, and Splunk Edge Hub can carry their
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
- Product-fit audit: [`src/splunk_uc/audits/uc_product_fit.py`](../../src/splunk_uc/audits/uc_product_fit.py), rules and review schemas under [`schemas/`](../../schemas/)

## Alternatives considered

- **Fold `products` into `premiumApps`** — rejected; `premiumApps` is a
  licensing signal and many platform use cases list a premium app they run on.
- **Extend `data/equipment-app-map.json`** — rejected; it maps equipment slugs
  to Splunkbase<sup class="ref">[<a href="#ref-7">7</a>]</sup> apps for the picker, not use cases to products.
- **Branch on product id in each consumer** — rejected; every new product would
  touch every consumer.
- **Put non-SPL artifacts in `spl`** — rejected; it breaks every SPL audit and
  the `q` contract.

## Links

- Registry: [`data/splunk-products.json`](../../data/splunk-products.json)
- Ledger: [ADR-0016](0016-permanent-uc-identifiers.md), [`data/id-ledger.json`](../../data/id-ledger.json)

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Cloud Platform Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Edge Hub Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/EdgeHub

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk Observability Cloud Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/observability/en/

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk SOAR (Cloud) Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SOARonprem

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

### Related repository documents

- [`docs/adr/0015-cost-field-group.md`](0015-cost-field-group.md)
- [`docs/adr/0016-permanent-uc-identifiers.md`](0016-permanent-uc-identifiers.md)

### Cited by

- [`AGENTS.md`](../../AGENTS.md)
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md)
- [`docs/adr/README.md`](README.md)
- [`docs/use-case-fields.md`](../use-case-fields.md)

<!-- END-AUTOGENERATED-SOURCES -->
