---
id: "7.4.10"
title: "Databricks Cluster Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.10 · Databricks Cluster Utilization

## Description

Cluster DBU hours, worker counts, and idle time reveal over-provisioned pools and jobs that keep clusters alive unnecessarily.

## Value

Cluster DBU hours, worker counts, and idle time reveal over-provisioned pools and jobs that keep clusters alive unnecessarily.

## Implementation

Ingest cluster lifecycle and DBU billing lines. Alert on clusters RUNNING >8h with low task activity (correlate with job logs). Normalize fields from your workspace audit pipeline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Databricks audit logs, cluster events API, `system.billing.usage`.
• Ensure the following data sources are available: `clusters` API events, billing export.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest cluster lifecycle and DBU billing lines. Alert on clusters RUNNING >8h with low task activity (correlate with job logs). Normalize fields from your workspace audit pipeline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=databricks sourcetype="databricks:cluster_event"
| where event_type IN ("RUNNING","TERMINATED")
| bin _time span=1d
| stats sum(uptime_seconds) as uptime, dc(cluster_id) as clusters by, _time
| eval dbu_estimate=uptime/3600*0.1
```

Understanding this SPL

**Databricks Cluster Utilization** — Cluster DBU hours, worker counts, and idle time reveal over-provisioned pools and jobs that keep clusters alive unnecessarily.

Documented **Data sources**: `clusters` API events, billing export. **App/TA** (typical add-on context): Databricks audit logs, cluster events API, `system.billing.usage`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: databricks; **sourcetype**: databricks:cluster_event. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=databricks, sourcetype="databricks:cluster_event". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where event_type IN ("RUNNING","TERMINATED")` — typically the threshold or rule expression for this monitoring goal.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **dbu_estimate** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DBU per day), Table (long-running clusters), Heatmap (cluster × hour utilization).

## SPL

```spl
index=databricks sourcetype="databricks:cluster_event"
| where event_type IN ("RUNNING","TERMINATED")
| bin _time span=1d
| stats sum(uptime_seconds) as uptime, dc(cluster_id) as clusters by, _time
| eval dbu_estimate=uptime/3600*0.1
```

## Visualization

Line chart (DBU per day), Table (long-running clusters), Heatmap (cluster × hour utilization).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
