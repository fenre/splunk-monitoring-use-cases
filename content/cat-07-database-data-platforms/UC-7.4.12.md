---
id: "7.4.12"
title: "BigQuery Cost Anomalies"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.12 · BigQuery Cost Anomalies

## Description

Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

## Value

Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

## Implementation

Ingest completed jobs daily. Alert on project-day cost outliers. Drill into `job_id` for top offenders. Integrate with GCP billing export for ground truth.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: BigQuery `INFORMATION_SCHEMA.JOBS`, billing export to Splunk.
• Ensure the following data sources are available: `total_bytes_billed`, `total_slot_ms`, `creation_time`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest completed jobs daily. Alert on project-day cost outliers. Drill into `job_id` for top offenders. Integrate with GCP billing export for ground truth.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="bigquery:jobs"
| bin _time span=1d
| stats sum(total_bytes_billed) as bytes by project_id, user_email, _time
| eventstats avg(bytes) as avg_b, stdev(bytes) as s by project_id
| where bytes > avg_b + 3*s
| eval gb=round(bytes/1073741824,2)
```

Understanding this SPL

**BigQuery Cost Anomalies** — Sudden jumps in bytes billed or slot usage often trace to one bad query or new scheduled job. Statistical alerting limits surprise invoices.

Documented **Data sources**: `total_bytes_billed`, `total_slot_ms`, `creation_time`. **App/TA** (typical add-on context): BigQuery `INFORMATION_SCHEMA.JOBS`, billing export to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: bigquery:jobs. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="bigquery:jobs". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by project_id, user_email, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eventstats` rolls up events into metrics; results are split **by project_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where bytes > avg_b + 3*s` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **gb** — often to normalize units, derive a ratio, or prepare for thresholds.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily bytes billed), Table (anomalous days/projects), Bar chart (top users by cost).

## SPL

```spl
index=datawarehouse sourcetype="bigquery:jobs"
| bin _time span=1d
| stats sum(total_bytes_billed) as bytes by project_id, user_email, _time
| eventstats avg(bytes) as avg_b, stdev(bytes) as s by project_id
| where bytes > avg_b + 3*s
| eval gb=round(bytes/1073741824,2)
```

## Visualization

Line chart (daily bytes billed), Table (anomalous days/projects), Bar chart (top users by cost).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
