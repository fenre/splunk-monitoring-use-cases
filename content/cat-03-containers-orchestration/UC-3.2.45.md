---
id: "3.2.45"
title: "Admission Webhook Latency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.45 · Admission Webhook Latency

## Description

P95/P99 webhook latency drives API server tail latency; isolating slow validating/mutating hooks prevents global API degradation.

## Value

P95/P99 webhook latency drives API server tail latency; isolating slow validating/mutating hooks prevents global API degradation.

## Implementation

Same histogram as UC-3.2.21; emphasize percentile SLOs per webhook `name` and `operation`. Page on P99 >1s for production webhooks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (apiserver metrics).
• Ensure the following data sources are available: `sourcetype=kube:apiserver`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Same histogram as UC-3.2.21; emphasize percentile SLOs per webhook `name` and `operation`. Page on P99 >1s for production webhooks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats perc95(_value) as p95, perc99(_value) as p99 by name, operation, _time
| where p95>0.25 OR p99>1
| sort -p99
```

Understanding this SPL

**Admission Webhook Latency** — P95/P99 webhook latency drives API server tail latency; isolating slow validating/mutating hooks prevents global API degradation.

Documented **Data sources**: `sourcetype=kube:apiserver`. **App/TA** (typical add-on context): Splunk OTel Collector (apiserver metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:apiserver. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:apiserver". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by name, operation, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where p95>0.25 OR p99>1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p95/p99 by webhook), Table (webhook, p99), Heatmap.

## SPL

```spl
index=k8s sourcetype="kube:apiserver" metric_name="apiserver_admission_webhook_admission_duration_seconds"
| bin _time span=5m
| stats perc95(_value) as p95, perc99(_value) as p99 by name, operation, _time
| where p95>0.25 OR p99>1
| sort -p99
```

## Visualization

Line chart (p95/p99 by webhook), Table (webhook, p99), Heatmap.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
