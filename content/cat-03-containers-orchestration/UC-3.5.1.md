---
id: "3.5.1"
title: "Istio Mesh Traffic Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.1 · Istio Mesh Traffic Monitoring

## Description

Baseline and anomaly detection on east-west traffic prevents silent degradation and helps isolate failing workloads before user impact spreads.

## Value

Baseline and anomaly detection on east-west traffic prevents silent degradation and helps isolate failing workloads before user impact spreads.

## Implementation

Deploy the OTel Collector with a Prometheus receiver targeting Istio workload and ingress scrape configs (per Istio observability docs). Forward metrics to Splunk via OTLP or Splunk HEC. Normalize `destination_service_name` and `response_code` labels into dimensions. Build baselines per service pair and alert on sustained error-rate spikes versus historical traffic.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (Prometheus receiver scraping Istio sidecar `15090`), `istio-mixer`/`istio` telemetry.
• Ensure the following data sources are available: `sourcetype=otel:metrics` or `sourcetype=prometheus:istio`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy the OTel Collector with a Prometheus receiver targeting Istio workload and ingress scrape configs (per Istio observability docs). Forward metrics to Splunk via OTLP or Splunk HEC. Normalize `destination_service_name` and `response_code` labels into dimensions. Build baselines per service pair and alert on sustained error-rate spikes versus historical traffic.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")
| eval rc=tonumber(response_code)
| stats sum(value) as requests by destination_service_name, reporter, rc
| eval is_error=if(rc>=500 OR rc=0 OR isnull(rc), 1, 0)
| stats sum(requests) as total, sum(eval(if(is_error=1, requests, 0))) as err by destination_service_name
| eval err_rate=round(100*err/total, 2)
| where err_rate > 1
| sort -err_rate
```

Understanding this SPL

**Istio Mesh Traffic Monitoring** — Baseline and anomaly detection on east-west traffic prevents silent degradation and helps isolate failing workloads before user impact spreads.

Documented **Data sources**: `sourcetype=otel:metrics` or `sourcetype=prometheus:istio`. **App/TA** (typical add-on context): Splunk OTel Collector (Prometheus receiver scraping Istio sidecar `15090`), `istio-mixer`/`istio` telemetry. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: otel:metrics, prometheus:istio. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="otel:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **rc** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by destination_service_name, reporter, rc** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **is_error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by destination_service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **err_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where err_rate > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (requests and 5xx by destination), Table (top error rates by service), Single value (mesh-wide error %).

## SPL

```spl
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where like(metric_name, "istio_requests_total%") OR like(name, "istio_requests_total%")
| eval rc=tonumber(response_code)
| stats sum(value) as requests by destination_service_name, reporter, rc
| eval is_error=if(rc>=500 OR rc=0 OR isnull(rc), 1, 0)
| stats sum(requests) as total, sum(eval(if(is_error=1, requests, 0))) as err by destination_service_name
| eval err_rate=round(100*err/total, 2)
| where err_rate > 1
| sort -err_rate
```

## Visualization

Time chart (requests and 5xx by destination), Table (top error rates by service), Single value (mesh-wide error %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
