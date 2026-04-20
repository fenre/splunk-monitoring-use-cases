---
id: "7.3.10"
title: "Cloud Spanner Instance Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.10 · Cloud Spanner Instance Health

## Description

CPU utilization, hot spots, and replication delay for Spanner nodes indicate risk of write/read stalls on globally distributed data.

## Value

CPU utilization, hot spots, and replication delay for Spanner nodes indicate risk of write/read stalls on globally distributed data.

## Implementation

Ingest Spanner instance metrics per project. Alert on high CPU or increasing 99p latency metrics. Use query insights export for hot keys if enabled.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: GCP Monitoring TA, scripted export.
• Ensure the following data sources are available: `spanner.googleapis.com/instance/cpu/utilization`, `transaction_count`, `streaming_pull_response_count`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Spanner instance metrics per project. Alert on high CPU or increasing 99p latency metrics. Use query insights export for hot keys if enabled.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="gcp:monitoring" metric_type="spanner.googleapis.com/instance/cpu/utilization"
| timechart span=5m avg(value) as cpu_util by instance_id
| where cpu_util > 0.65
```

Understanding this SPL

**Cloud Spanner Instance Health** — CPU utilization, hot spots, and replication delay for Spanner nodes indicate risk of write/read stalls on globally distributed data.

Documented **Data sources**: `spanner.googleapis.com/instance/cpu/utilization`, `transaction_count`, `streaming_pull_response_count`. **App/TA** (typical add-on context): GCP Monitoring TA, scripted export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by instance_id** — ideal for trending and alerting on this use case.
• Filters the current rows with `where cpu_util > 0.65` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU and latency), Table (instances over SLO), Heatmap (instance × region).

## SPL

```spl
index=gcp sourcetype="gcp:monitoring" metric_type="spanner.googleapis.com/instance/cpu/utilization"
| timechart span=5m avg(value) as cpu_util by instance_id
| where cpu_util > 0.65
```

## Visualization

Line chart (CPU and latency), Table (instances over SLO), Heatmap (instance × region).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
