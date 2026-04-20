---
id: "3.5.8"
title: "Circuit Breaker Trips"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.8 · Circuit Breaker Trips

## Description

Outlier detection and open circuits protect the mesh; frequent trips signal upstream saturation or bad health checks that need capacity or code fixes.

## Value

Outlier detection and open circuits protect the mesh; frequent trips signal upstream saturation or bad health checks that need capacity or code fixes.

## Implementation

Scrape Istio/Envoy Prometheus endpoints (port 15090) with OTel Prometheus receiver. Map overflow and ejection counters to Splunk metrics. Correlate trips with deploy times and upstream latency. Alert when overflow rate accelerates versus steady-state for a cluster.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (Envoy/Istio Prometheus metrics).
• Ensure the following data sources are available: `sourcetype=prometheus:istio` or `sourcetype=otel:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape Istio/Envoy Prometheus endpoints (port 15090) with OTel Prometheus receiver. Map overflow and ejection counters to Splunk metrics. Correlate trips with deploy times and upstream latency. Alert when overflow rate accelerates versus steady-state for a cluster.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers (sourcetype="prometheus:istio" OR sourcetype="otel:metrics")
| where match(metric_name, "envoy_cluster_upstream_rq_pending_overflow") OR match(metric_name, "circuit_breakers.*overflow")
| stats sum(value) as trips by cluster_name, destination_service_name
| where trips>0
| sort -trips
```

Understanding this SPL

**Circuit Breaker Trips** — Outlier detection and open circuits protect the mesh; frequent trips signal upstream saturation or bad health checks that need capacity or code fixes.

Documented **Data sources**: `sourcetype=prometheus:istio` or `sourcetype=otel:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector (Envoy/Istio Prometheus metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: prometheus:istio, otel:metrics. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="prometheus:istio". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(metric_name, "envoy_cluster_upstream_rq_pending_overflow") OR match(metric_name, "circuit_breakers.*overflow")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cluster_name, destination_service_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where trips>0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (overflow counters by cluster), Table (cluster, trips, destination), Bar chart (trips per namespace).

## SPL

```spl
index=containers (sourcetype="prometheus:istio" OR sourcetype="otel:metrics")
| where match(metric_name, "envoy_cluster_upstream_rq_pending_overflow") OR match(metric_name, "circuit_breakers.*overflow")
| stats sum(value) as trips by cluster_name, destination_service_name
| where trips>0
| sort -trips
```

## Visualization

Time chart (overflow counters by cluster), Table (cluster, trips, destination), Bar chart (trips per namespace).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
