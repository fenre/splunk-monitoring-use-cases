---
id: "4.3.21"
title: "Cloud Run Revision Traffic and Error Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.21 · Cloud Run Revision Traffic and Error Rate

## Description

Cloud Run revision traffic and errors indicate service health. Supports canary and blue-green deployment monitoring.

## Value

Cloud Run revision traffic and errors indicate service health. Supports canary and blue-green deployment monitoring.

## Implementation

Collect Cloud Run metrics. Alert on 5xx rate >1% or container instance count spike. Monitor cold start and latency. Track traffic split across revisions for canary analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Run metrics (request_count, container_instance_count, container_cpu_utilizations).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Cloud Run metrics. Alert on 5xx rate >1% or container instance count spike. Monitor cold start and latency. Track traffic split across revisions for canary analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count"
| timechart span=5m sum(value) by resource.labels.revision_name
| eval error_rate = request_count_5xx / request_count * 100
| where error_rate > 1
```

Understanding this SPL

**Cloud Run Revision Traffic and Error Rate** — Cloud Run revision traffic and errors indicate service health. Supports canary and blue-green deployment monitoring.

Documented **Data sources**: Cloud Run metrics (request_count, container_instance_count, container_cpu_utilizations). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource.labels.revision_name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (requests, errors by revision), Table (revision, error rate), Gauge (traffic % by revision).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count"
| timechart span=5m sum(value) by resource.labels.revision_name
| eval error_rate = request_count_5xx / request_count * 100
| where error_rate > 1
```

## Visualization

Line chart (requests, errors by revision), Table (revision, error rate), Gauge (traffic % by revision).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
