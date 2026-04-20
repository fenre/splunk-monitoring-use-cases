---
id: "4.3.12"
title: "Cloud SQL Instance Metrics and Replication Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.12 · Cloud SQL Instance Metrics and Replication Lag

## Description

Cloud SQL CPU, storage, and replication lag impact application performance and DR. Monitoring supports capacity and replica health.

## Value

Cloud SQL CPU, storage, and replication lag impact application performance and DR. Monitoring supports capacity and replica health.

## Implementation

Collect Cloud SQL metrics. Alert when replica_lag > 10 seconds or CPU utilization > 80%. Monitor disk utilization and connection count. Enable slow query log for query-level analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring (cloudsql.googleapis.com/database/cpu/utilization, replication/replica_lag).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Cloud SQL metrics. Alert when replica_lag > 10 seconds or CPU utilization > 80%. Monitor disk utilization and connection count. Enable slow query log for query-level analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/replication/replica_lag"
| where value > 10
| timechart span=5m avg(value) by resource.labels.database_id
```

Understanding this SPL

**Cloud SQL Instance Metrics and Replication Lag** — Cloud SQL CPU, storage, and replication lag impact application performance and DR. Monitoring supports capacity and replica health.

Documented **Data sources**: Cloud Monitoring (cloudsql.googleapis.com/database/cpu/utilization, replication/replica_lag). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where value > 10` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource.labels.database_id** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU, lag, connections by instance), Table (instance, lag), Gauge (replica lag).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudsql.googleapis.com/database/replication/replica_lag"
| where value > 10
| timechart span=5m avg(value) by resource.labels.database_id
```

## Visualization

Line chart (CPU, lag, connections by instance), Table (instance, lag), Gauge (replica lag).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
