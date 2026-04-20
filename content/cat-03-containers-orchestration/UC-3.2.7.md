---
id: "3.2.7"
title: "Control Plane Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.7 · Control Plane Health

## Description

The control plane (API server, etcd, scheduler, controller-manager) is the brain of Kubernetes. Degradation affects all cluster operations.

## Value

The control plane (API server, etcd, scheduler, controller-manager) is the brain of Kubernetes. Degradation affects all cluster operations.

## Implementation

Configure OTel Collector to scrape control plane metrics endpoints (/metrics on each component). Monitor API server request latency, etcd request duration, scheduler binding latency. Alert on P99 latency >1s or error rates >1%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, control plane component metrics.
• Ensure the following data sources are available: API server metrics, etcd metrics, scheduler/controller-manager logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure OTel Collector to scrape control plane metrics endpoints (/metrics on each component). Monitor API server request latency, etcd request duration, scheduler binding latency. Alert on P99 latency >1s or error rates >1%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:apiserver"
| timechart span=5m avg(apiserver_request_duration_seconds) as avg_latency by verb
| where avg_latency > 1
```

Understanding this SPL

**Control Plane Health** — The control plane (API server, etcd, scheduler, controller-manager) is the brain of Kubernetes. Degradation affects all cluster operations.

Documented **Data sources**: API server metrics, etcd metrics, scheduler/controller-manager logs. **App/TA** (typical add-on context): Splunk OTel Collector, control plane component metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:apiserver. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:apiserver". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by verb** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_latency > 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency by verb), Single value (error rate), Multi-panel dashboard per component.

## SPL

```spl
index=k8s sourcetype="kube:apiserver"
| timechart span=5m avg(apiserver_request_duration_seconds) as avg_latency by verb
| where avg_latency > 1
```

## Visualization

Line chart (latency by verb), Single value (error rate), Multi-panel dashboard per component.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
