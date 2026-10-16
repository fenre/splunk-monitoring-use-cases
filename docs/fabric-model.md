# Use case fabric

The fabric is a normalized model for this catalogue, in the same sense that
the Splunk Common Information Model is a normalized model for event data.
`sourcetype:pan:traffic`, `product:paloalto`, and `outcome:lower_security_risk`
mean the same thing on every use case, and each one links to the entities
connected to it.

Narrative fields (`title`, `description`, `value`, SPL, explanations) are
not part of the fabric and are never rewritten to populate it.

## Entity types

| Type | Id | Canonical fields | Where the values live |
|---|---|---|---|
| `usecase` | The sidecar id, `5.1.1` | The sidecar itself | `content/cat-*/UC-*.json` |
| `sourcetype` | Slug of the canonical spelling (`pan-traffic`) | `canonical`, `aliases`, `vendorProduct`, `addon`, `cimDatasets`, `usageCount` | [`registries/sourcetypes.json`](../registries/sourcetypes.json) |
| `vendorProduct` | Equipment slug (`paloalto`) | `vendor`, `product`, `kind`, `aliases`, `models`, `usageCount` | [`registries/vendor-products.json`](../registries/vendor-products.json) |
| `addon` | Splunkbase app id (`7523`) | `name`, `folderName`, `aliases`, `inSplunkbaseCatalog`, `usageCount` | [`registries/addons.json`](../registries/addons.json) |
| `cimDataset` | Slug of the model or `model-dataset` | `model`, `dataset`, `usageCount` | [`registries/cim.json`](../registries/cim.json) `datasets` |
| `cimField` | Slug of `dataset-field` | `name`, `dataset`, `usageCount` | [`registries/cim.json`](../registries/cim.json) `fields` |
| `complianceControl` | Slug of `{regulation}-{version}-{clause}` (`gdpr-2016-679-art-5`). The `obligationRef` is an alias. | The clause already stored on the sidecar | `compliance[]` |
| `industry` | Slug of the canonical industry name | `name`, `aliases`, `usageCount` | [`registries/industries.json`](../registries/industries.json) |
| `businessOutcome` | Snake-case id | `label`, `phrases`, `usageCount` | [`registries/business-outcomes.json`](../registries/business-outcomes.json) |
| `businessArea` | Snake-case id | `label`, `phrases`, `usageCount` | [`registries/business-areas.json`](../registries/business-areas.json) |
| `persona` | Snake-case id | `label`, `phrases`, `usageCount` | [`registries/personas.json`](../registries/personas.json) |

`usageCount` is the number of use cases that already state the value (or, for
seller concepts, the number whose title, description, value, or plain-language
explanation contains one of the concept's phrases). It is not an assignment.

Ids used in URLs are lowercase slugs: letters, digits, and hyphens. The
canonical sourcetype spelling, including its colons and original case, is
the `canonical` field. Looking up an alias resolves to that id.

## Allowed CIM models

A `cimModels[]` value or a `datamodel=` clause is a CIM dataset only when its
normalised name is one of:

`Alerts`, `Application_State`, `Authentication`, `Certificates`, `Change`,
`Compute_Inventory`, `Data_Access`, `Databases`, `DLP`, `Email`, `Endpoint`,
`Interprocess_Messaging`, `Intrusion_Detection`, `Inventory`, `JVM`,
`Malware`, `Network_Resolution`, `Network_Sessions`, `Network_Traffic`,
`Performance`, `Splunk_Audit`, `Ticket_Management`, `Updates`,
`Vulnerabilities`, `Web`.

`Change_Analysis` is recorded as an alias of `Change`, which is the name the
CIM manual uses for that data model. Any other spelling is listed in
[`registries/ambiguous.json`](../registries/ambiguous.json) and is not mapped.

A dotted field (`All_Traffic.src`) is kept only when the dataset node is in
the CIM manual's node list and the field name is in the curated CIM field
list stored in the miner. A bare `requiredFields` entry with no dataset is
listed as ambiguous. It is not attached to a dataset by guesswork.

## Seller concepts

Business areas are not technology categories and they are not industries.
Personas are not the `owner` enum (`CISO`, `DPO`, `CFO`, and the rest). The
allowed ids are the entries in the three seller registries. A phrase list is
the only evidence the miner counts.

Outcomes (12): `lower_security_risk`, `faster_incident_response`,
`prove_compliance`, `reduce_downtime`, `protect_sensitive_data`,
`control_privileged_access`, `detect_fraud`, `improve_service_reliability`,
`reduce_operational_cost`, `contain_threats`, `protect_ot_safety`,
`improve_change_safety`.

## Relationships

Every relationship has one predicate, a direction, a provenance of `authored`
or `inferred`, and a confidence from 0 to 1. Explicit facts already written
on a sidecar are `authored` with confidence 1. Enrichment may add `inferred`
links later. It does not replace authored ones.

| Predicate | From | To |
|---|---|---|
| `uses` | usecase | sourcetype |
| `producedBy` | sourcetype | addon |
| `emittedBy` | sourcetype | vendorProduct |
| `mapsTo` | sourcetype | cimDataset |
| `requiresField` | usecase | cimField |
| `partOf` | cimField | cimDataset |
| `covers` | usecase | complianceControl |
| `requires` | usecase | usecase |
| `runsOn` | usecase | vendorProduct |
| `servesOutcome` | usecase | businessOutcome |
| `inArea` | usecase | businessArea |
| `forPersona` | usecase | persona |
| `inIndustry` | usecase | industry |

Two use cases are connected through data when they share a sourcetype or a
CIM dataset. That view is derived when someone asks. It is not stored as its
own edge. The weight is how many entities they share.

## How a value is placed

`python -m splunk_uc mine-fabric-registries --write` rebuilds the registries
from `content/cat-*/UC-*.json`. `--check` fails when the committed files drift.

Sourcetype candidates are explicit `sourcetype=` tokens in `spl`, `cimSpl`,
and `dataSources`, plus a quoted token in `dataSources` when it contains a
colon or sits next to the word sourcetype. Spellings that differ only by case
share one entry. The most common spelling is canonical. The others are aliases.

A sourcetype is linked to a vendor product, add-on, or CIM dataset only when
every use case that names exactly one candidate agrees, and at least two use
cases vote. Splunk platform slugs (`splunk_es`, `itsi`, and the other
`kind=splunk-platform` rows) do not vote for `emittedBy`, because they are
not the device that emits the log. A disagreement is a conflict: the link is
left empty and the canonical name is listed in `ambiguous.json`.

Vendor products are the `EQUIPMENT` rows in `tools/build/enrichment.py`.
Models come from `equipmentModels` values that start with a known equipment
id. An `equipmentModels` string with no such prefix is ambiguous.

Add-ons are keyed by the Splunkbase id on `splunkbaseApps[]` or by a
`Splunkbase NNN` citation. The name comes from `data/splunkbase-catalog.json`
when the id is in that cache.

Industries are the free-text `industry` field. Case, whitespace, and `&` /
`and` fold together. A string that is a sentence, or that appears on only one
use case, is ambiguous rather than a new industry.

MAC addresses, IPv6 literals, wildcards, and tokens that are not sourcetype
names are ambiguous. Nothing in this pass edits a use case.

## Query surfaces

`python -m splunk_uc build-fabric --check` resolves every sidecar against
the registries. Explicit facts are `authored` at confidence 1. An `app`
token or sourcetype spelling that matches a registry alias is a real edge.
A value that does not match is listed in the build report.

The build writes:

- `entities.parquet` and `relationships.parquet` when pyarrow is installed
  (`pip install -e '.[build]'`). Compression is off and rows are sorted so
  two builds in one environment match.
- `/api/v1/fabric/index.json` maps every alias to its canonical entity.
  `/api/v1/fabric/{type}/{id}.json` is the entity plus neighbours grouped
  by predicate. `pan:traffic` and `Splunk_TA_paloalto` resolve through the
  index. A shared alias is listed, not guessed.
- `fabric/facets.json` has a count for every sourcetype, product, add-on,
  and CIM dataset, plus pairwise intersections for the common values. The
  catalogue's advanced filters use the top values.
- Search indexes `fx`, the alias text of the linked entities, so `Palo Alto`,
  `paloalto`, and the search synonym `PAN` find the same product.
- `graph-data.json` is the aggregated view `graph.html` already renders.
  Pillars stay a presentation rollup. `fabric/graph-full.json` is the same
  relationships with use cases as nodes.

`data/fabric-resolution-baseline.json` records the share of sidecars whose
`app` signals and explicit sourcetypes resolve. `--check` fails if either
rate drops.

## Schemas

Each registry file points at its JSON Schema under
[`schemas/fabric/`](../schemas/fabric/).
