# DA-ITSI-monitoring-use-cases — ITSI Content Pack

A Splunk IT Service Intelligence (ITSI) content pack derived from the
[Splunk Monitoring Use Cases](https://github.com/fenre/splunk-monitoring-use-cases)
catalog.  Ships a seeded set of **KPI base searches**, **KPI templates**,
**threshold templates**, and **service templates** that cover the most
common infrastructure health indicators.

## What it contains

| Configuration                                    | Stanzas | Purpose                                                                 |
|--------------------------------------------------|--------:|-------------------------------------------------------------------------|
| `default/itsi_kpi_base_search.conf`              | 6       | Shared base searches (CPU / memory / disk / network / VMware / HTTP / K8s) |
| `default/itsi_kpi_threshold_template.conf`       | 3       | Static threshold bands for percent-usage, availability, and error-count KPIs |
| `default/itsi_kpi_template.conf`                 | 4       | KPI bundles: Linux host, Windows host, Network, Web availability        |
| `default/itsi_service_template.conf`             | 3       | Service templates: Linux host, Windows host, Network device             |
| `metadata/default.meta`                          | —       | Global export so ITSI can consume the objects from any app context      |

## Prerequisites

- Splunk Enterprise ≥ 9.0 on search heads that run ITSI.
- Splunk IT Service Intelligence ≥ 4.17 (ML-Assisted Thresholding support).
- Upstream data source add-ons installed and producing events in the indexes
  referenced by each base search (e.g. `Splunk_TA_nix` for `sourcetype=cpu`).

## Installation

1. Download `DA-ITSI-monitoring-use-cases-<version>.spl` from the
   [Releases page](https://github.com/fenre/splunk-monitoring-use-cases/releases)
   or run `bash scripts/package_itsi.sh` locally.
2. In Splunk Web: *Apps → Manage Apps → Install app from file*.
3. In ITSI: *Configuration → KPI Base Searches* — verify the six base
   searches appear.  Adjust `entity_alias_filtering_fields` if your entity
   alias is not `host`.
4. *Configuration → Service Templates* — select any template and click
   *Create Service* to spin up a linked service.  Edit entity rules to
   match your fleet naming conventions (`linux-*`, `win-*`, `net-*`).
5. Run *Rebuild Entity Membership* on each service after tweaking entity
   rules.

## Extending the content pack

The base searches in this pack are hand-curated from the catalog's
**Quick Start** use cases.  The full catalog contains 6,400+ use cases;
use `scripts/build_itsi_cp.py` (to be added in a future release) to
auto-generate additional KPI base searches from catalog data.

General recipe for adding a UC as a KPI:

1. Pick a UC whose SPL ends in `| stats <func>(field) AS metric BY host`.
   Aggregation must yield a numeric field per entity.
2. Copy the SPL into a new `[itsi_uc_<name>]` stanza in
   `itsi_kpi_base_search.conf` (prefer to merge it into an existing base
   search if the metric can be computed from the same indexes).
3. Add the metric to the base search's `metrics` JSON array.
4. Reference the metric from an existing or new KPI template in
   `itsi_kpi_template.conf`.
5. Link the KPI template to a service template in
   `itsi_service_template.conf`.

## Threshold tuning

All shipped threshold templates use **static** severity bands.  For
production, switch to adaptive thresholds by setting
`adaptive_thresholds_is_enabled = 1` once you have ≥ 7 days of data — or
use ML-Assisted Thresholding in the ITSI UI.

## Support and licence

- Upstream project: <https://github.com/fenre/splunk-monitoring-use-cases>
- Licence: MIT (see `LICENSE`).
- Not an officially supported Splunk product — review every base search
  before enabling schedules.
