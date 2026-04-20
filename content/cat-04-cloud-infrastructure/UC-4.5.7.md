---
id: "4.5.7"
title: "GCP Cloud Functions Memory Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.5.7 · GCP Cloud Functions Memory Utilization

## Description

Memory pressure causes OOM terminations and retries; tracking user memory against allocation prevents instability and guides memory settings per function.

## Value

Memory pressure causes OOM terminations and retries; tracking user memory against allocation prevents instability and guides memory settings per function.

## Implementation

Export Cloud Monitoring metrics for Cloud Functions to Splunk via the GCP add-on. Join max memory usage with deployed memory configuration from labels or an asset lookup. Alert when utilization consistently approaches the configured limit (for example >85% of allocated memory).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (Cloud Functions metrics).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export Cloud Monitoring metrics for Cloud Functions to Splunk via the GCP add-on. Join max memory usage with deployed memory configuration from labels or an asset lookup. Alert when utilization consistently approaches the configured limit (for example >85% of allocated memory).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"
| timechart span=5m avg(value) as avg_bytes, max(value) as max_bytes by metric.labels.function_name
| eval max_mb=round(max_bytes/1048576, 2)
| where max_mb > 0
```

Understanding this SPL

**GCP Cloud Functions Memory Utilization** — Memory pressure causes OOM terminations and retries; tracking user memory against allocation prevents instability and guides memory settings per function.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (Cloud Functions metrics). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric.labels.function_name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **max_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where max_mb > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (avg/max memory by function), Gauge (peak vs allocation), Table (function_name, max_mb, allocation_mb).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="cloudfunctions.googleapis.com/function/user_memory_bytes"
| timechart span=5m avg(value) as avg_bytes, max(value) as max_bytes by metric.labels.function_name
| eval max_mb=round(max_bytes/1048576, 2)
| where max_mb > 0
```

## Visualization

Line chart (avg/max memory by function), Gauge (peak vs allocation), Table (function_name, max_mb, allocation_mb).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
