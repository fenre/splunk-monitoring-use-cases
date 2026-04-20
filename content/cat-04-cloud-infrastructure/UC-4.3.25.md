---
id: "4.3.25"
title: "BigQuery Slot Usage Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.25 · BigQuery Slot Usage Monitoring

## Description

Slot contention slows queries and raises cost; tracking slot usage versus reservation prevents interactive BI outages and runaway batch jobs.

## Value

Slot contention slows queries and raises cost; tracking slot usage versus reservation prevents interactive BI outages and runaway batch jobs.

## Implementation

Ingest Cloud Monitoring metrics for slot usage and optional `JOBS_BY_PROJECT` exports. Alert when usage exceeds reservation plus burst buffer or sustained elevation vs 7-day baseline. Dashboard by reservation assignment and job type.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`, BigQuery INFORMATION_SCHEMA export.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`bigquery.googleapis.com/slot/usage`), audit exports to Pub/Sub.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Cloud Monitoring metrics for slot usage and optional `JOBS_BY_PROJECT` exports. Alert when usage exceeds reservation plus burst buffer or sustained elevation vs 7-day baseline. Dashboard by reservation assignment and job type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="bigquery.googleapis.com/slot/usage"
| stats latest(value) as slot_seconds by resource.labels.project_id, bin(_time, 5m)
| eventstats avg(slot_seconds) as baseline by resource.labels.project_id
| where slot_seconds > baseline * 1.5
| table _time resource.labels.project_id slot_seconds baseline
```

Understanding this SPL

**BigQuery Slot Usage Monitoring** — Slot contention slows queries and raises cost; tracking slot usage versus reservation prevents interactive BI outages and runaway batch jobs.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`bigquery.googleapis.com/slot/usage`), audit exports to Pub/Sub. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`, BigQuery INFORMATION_SCHEMA export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.project_id, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by resource.labels.project_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where slot_seconds > baseline * 1.5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **BigQuery Slot Usage Monitoring**): table _time resource.labels.project_id slot_seconds baseline

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Area chart (slot usage vs cap), Table (project, peak slots), Single value (utilization %).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="bigquery.googleapis.com/slot/usage"
| stats latest(value) as slot_seconds by resource.labels.project_id, bin(_time, 5m)
| eventstats avg(slot_seconds) as baseline by resource.labels.project_id
| where slot_seconds > baseline * 1.5
| table _time resource.labels.project_id slot_seconds baseline
```

## Visualization

Area chart (slot usage vs cap), Table (project, peak slots), Single value (utilization %).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
