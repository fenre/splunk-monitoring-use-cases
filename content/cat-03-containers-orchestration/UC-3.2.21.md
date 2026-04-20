---
id: "3.2.21"
title: "Kubernetes Admission Webhook Latency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.21 · Kubernetes Admission Webhook Latency

## Description

Slow webhooks causing API server delays and impacting cluster operations.

## Value

Slow webhooks causing API server delays and impacting cluster operations.

## Implementation

Scrape API server metrics (typically via kube-apiserver /metrics or OTel Collector). The `apiserver_admission_webhook_admission_duration_seconds` histogram has labels `name` (webhook) and `operation`. Alert when P99 or average exceeds 500ms. Slow webhooks (e.g. OPA, Kyverno, cert-manager) block all API requests. Identify and optimize or remove slow webhooks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes.
• Ensure the following data sources are available: apiserver metrics (`apiserver_admission_webhook_admission_duration_seconds`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape API server metrics (typically via kube-apiserver /metrics or OTel Collector). The `apiserver_admission_webhook_admission_duration_seconds` histogram has labels `name` (webhook) and `operation`. Alert when P99 or average exceeds 500ms. Slow webhooks (e.g. OPA, Kyverno, cert-manager) block all API requests. Identify and optimize or remove slow webhooks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats avg(_value) as avg_sec, max(_value) as max_sec, count by webhook, operation, _time
| where avg_sec > 0.5 OR max_sec > 2
| table _time webhook operation avg_sec max_sec count
| sort -avg_sec
```

Understanding this SPL

**Kubernetes Admission Webhook Latency** — Slow webhooks causing API server delays and impacting cluster operations.

Documented **Data sources**: apiserver metrics (`apiserver_admission_webhook_admission_duration_seconds`). **App/TA** (typical add-on context): Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:apiserver. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:apiserver". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by webhook, operation, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_sec > 0.5 OR max_sec > 2` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes Admission Webhook Latency**): table _time webhook operation avg_sec max_sec count
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (webhook, operation, avg, max latency), Line chart (latency over time by webhook), Heatmap.

## SPL

```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats avg(_value) as avg_sec, max(_value) as max_sec, count by webhook, operation, _time
| where avg_sec > 0.5 OR max_sec > 2
| table _time webhook operation avg_sec max_sec count
| sort -avg_sec
```

## Visualization

Table (webhook, operation, avg, max latency), Line chart (latency over time by webhook), Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
