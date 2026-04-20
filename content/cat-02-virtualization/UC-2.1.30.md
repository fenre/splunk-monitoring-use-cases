---
id: "2.1.30"
title: "Storage DRS Recommendations and Actions"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.30 · Storage DRS Recommendations and Actions

## Description

Storage DRS (SDRS) balances VM storage across datastores within a datastore cluster. Frequent SDRS migrations indicate capacity or performance imbalance. Unapplied recommendations (when SDRS is in manual mode) mean datastores are unbalanced and latency may be inconsistent.

## Value

Storage DRS (SDRS) balances VM storage across datastores within a datastore cluster. Frequent SDRS migrations indicate capacity or performance imbalance. Unapplied recommendations (when SDRS is in manual mode) mean datastores are unbalanced and latency may be inconsistent.

## Implementation

Collect vCenter events via Splunk_TA_vmware. Track SDRS migration frequency per datastore cluster. Alert when manual-mode SDRS has unapplied recommendations older than 24 hours. Monitor datastore cluster balance — alert when any datastore deviates >20% from the cluster average utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect vCenter events via Splunk_TA_vmware. Track SDRS migration frequency per datastore cluster. Alert when manual-mode SDRS has unapplied recommendations older than 24 hours. Monitor datastore cluster balance — alert when any datastore deviates >20% from the cluster average utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:events" (event_type="StorageDrsRecommendation*" OR event_type="StorageMigratedEvent")
| eval action=case(match(event_type, "Recommendation"), "Recommended", event_type="StorageMigratedEvent", "Migrated")
| stats count by action, datastore_cluster
| sort -count
| table datastore_cluster, action, count
```

Understanding this SPL

**Storage DRS Recommendations and Actions** — Storage DRS (SDRS) balances VM storage across datastores within a datastore cluster. Frequent SDRS migrations indicate capacity or performance imbalance. Unapplied recommendations (when SDRS is in manual mode) mean datastores are unbalanced and latency may be inconsistent.

Documented **Data sources**: `sourcetype=vmware:events`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by action, datastore_cluster** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Storage DRS Recommendations and Actions**): table datastore_cluster, action, count


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (recommendations and actions), Bar chart (migrations per cluster), Line chart (cluster balance over time).

## SPL

```spl
index=vmware sourcetype="vmware:events" (event_type="StorageDrsRecommendation*" OR event_type="StorageMigratedEvent")
| eval action=case(match(event_type, "Recommendation"), "Recommended", event_type="StorageMigratedEvent", "Migrated")
| stats count by action, datastore_cluster
| sort -count
| table datastore_cluster, action, count
```

## Visualization

Table (recommendations and actions), Bar chart (migrations per cluster), Line chart (cluster balance over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
