---
id: "4.3.34"
title: "Dataflow Pipeline Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.34 · Dataflow Pipeline Health

## Description

Batch and streaming pipelines power analytics; failed jobs or high system lag delay downstream consumers.

## Value

Batch and streaming pipelines power analytics; failed jobs or high system lag delay downstream consumers.

## Implementation

Ingest job state changes (FAILED, UPDATED) from logging. Alert on sustained system lag for streaming jobs or failed batch completion. Dashboard worker CPU and shuffle errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`dataflow.googleapis.com/job/*`), Dataflow worker logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest job state changes (FAILED, UPDATED) from logging. Alert on sustained system lag for streaming jobs or failed batch completion. Dashboard worker CPU and shuffle errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="dataflow.googleapis.com/job/system_lag"
| stats latest(value) as lag_sec by resource.labels.job_name, bin(_time, 5m)
| where lag_sec > 300
| sort - lag_sec
```

Understanding this SPL

**Dataflow Pipeline Health** — Batch and streaming pipelines power analytics; failed jobs or high system lag delay downstream consumers.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`dataflow.googleapis.com/job/*`), Dataflow worker logs. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.job_name, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where lag_sec > 300` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (system lag), Table (job, state), Timeline (job failures).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="dataflow.googleapis.com/job/system_lag"
| stats latest(value) as lag_sec by resource.labels.job_name, bin(_time, 5m)
| where lag_sec > 300
| sort - lag_sec
```

## Visualization

Line chart (system lag), Table (job, state), Timeline (job failures).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
