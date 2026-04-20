---
id: "4.3.24"
title: "GCP Cloud Run Cold Start Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.24 · GCP Cloud Run Cold Start Rate

## Description

Serverless cold start impact on request latency. High cold start rates cause P99 latency spikes and timeouts for scale-to-zero services.

## Value

Serverless cold start impact on request latency. High cold start rates cause P99 latency spikes and timeouts for scale-to-zero services.

## Implementation

Use GCP Monitoring API (or Cloud Monitoring export) to ingest Cloud Run metrics. Request count and instance count indicate scale-to-zero; zero instances with requests implies cold starts. For detailed latency, ingest `run.googleapis.com/request_latencies` and `run.googleapis.com/container/startup_latencies`. Alert when cold start rate exceeds 5% or startup latency > 3s. Consider min instances for latency-critical services.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom (GCP Monitoring API).
• Ensure the following data sources are available: Cloud Run metrics (request_latencies, instance_count, container/startup_latencies).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use GCP Monitoring API (or Cloud Monitoring export) to ingest Cloud Run metrics. Request count and instance count indicate scale-to-zero; zero instances with requests implies cold starts. For detailed latency, ingest `run.googleapis.com/request_latencies` and `run.googleapis.com/container/startup_latencies`. Alert when cold start rate exceeds 5% or startup latency > 3s. Consider min instances for latency-critical services.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count" OR metric.type="run.googleapis.com/container/instance_count"
| eval metric_type=coalesce(metric.type, 'run.googleapis.com/request_count')
| stats sum(value) as requests, latest(value) as instances by resource.labels.service_name, metric_type, bin(_time, 5m)
| eval cold_start_indicator=if(instances=0 AND requests>0, 1, 0)
| stats sum(requests) as total_requests, sum(cold_start_indicator) as cold_start_events by resource.labels.service_name
| eval cold_start_pct=round(cold_start_events/total_requests*100, 1)
| where cold_start_pct > 5
| table resource.labels.service_name total_requests cold_start_events cold_start_pct
| sort -cold_start_pct
```

Understanding this SPL

**GCP Cloud Run Cold Start Rate** — Serverless cold start impact on request latency. High cold start rates cause P99 latency spikes and timeouts for scale-to-zero services.

Documented **Data sources**: Cloud Run metrics (request_latencies, instance_count, container/startup_latencies). **App/TA** (typical add-on context): Custom (GCP Monitoring API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **metric_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resource.labels.service_name, metric_type, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **cold_start_indicator** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by resource.labels.service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **cold_start_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where cold_start_pct > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **GCP Cloud Run Cold Start Rate**): table resource.labels.service_name total_requests cold_start_events cold_start_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (cold start % and startup latency by service over time), Table (service, cold starts, %), Single value (cold start rate).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="run.googleapis.com/request_count" OR metric.type="run.googleapis.com/container/instance_count"
| eval metric_type=coalesce(metric.type, 'run.googleapis.com/request_count')
| stats sum(value) as requests, latest(value) as instances by resource.labels.service_name, metric_type, bin(_time, 5m)
| eval cold_start_indicator=if(instances=0 AND requests>0, 1, 0)
| stats sum(requests) as total_requests, sum(cold_start_indicator) as cold_start_events by resource.labels.service_name
| eval cold_start_pct=round(cold_start_events/total_requests*100, 1)
| where cold_start_pct > 5
| table resource.labels.service_name total_requests cold_start_events cold_start_pct
| sort -cold_start_pct
```

## Visualization

Line chart (cold start % and startup latency by service over time), Table (service, cold starts, %), Single value (cold start rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
