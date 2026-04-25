<!-- AUTO-GENERATED from UC-3.5.10.json — DO NOT EDIT -->

---
id: "3.5.10"
title: "Ingress Gateway Latency"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.10 · Ingress Gateway Latency

## Description

North-south latency reflects TLS, auth, and routing at the edge; regressions here affect every external client before internal mesh metrics move.

## Value

North-south latency reflects TLS, auth, and routing at the edge; regressions here affect every external client before internal mesh metrics move.

## Implementation

Label ingress gateway access logs with `gateway_workload` or filter Kubernetes workload name. Export histogram or timer metrics (`istio_request_duration_milliseconds`) via OTel. Set SLO windows on p95/p99 per host and route. Compare canary vs stable gateway revisions during rollouts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (Istio ingress gateway metrics), Envoy access logs.
• Ensure the following data sources are available: `sourcetype=otel:metrics` or `sourcetype=envoy:access`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Label ingress gateway access logs with `gateway_workload` or filter Kubernetes workload name. Export histogram or timer metrics (`istio_request_duration_milliseconds`) via OTel. Set SLO windows on p95/p99 per host and route. Compare canary vs stable gateway revisions during rollouts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="envoy:access"
| where like(gateway_workload, "istio-ingress%") OR like(kubernetes_pod_name, "istio-ingress%")
| eval dur_ms=tonumber(duration_ms)
| timechart span=5m perc95(dur_ms) as p95_ms, perc99(dur_ms) as p99_ms by route_name
```

Understanding this SPL

**Ingress Gateway Latency** — North-south latency reflects TLS, auth, and routing at the edge; regressions here affect every external client before internal mesh metrics move.

Documented **Data sources**: `sourcetype=otel:metrics` or `sourcetype=envoy:access`. **App/TA** (typical add-on context): Splunk OTel Collector (Istio ingress gateway metrics), Envoy access logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: envoy:access. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="envoy:access". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where like(gateway_workload, "istio-ingress%") OR like(kubernetes_pod_name, "istio-ingress%")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **dur_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by route_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Time chart (p95/p99 latency by route), Geographic or by-AZ breakdown if multi-region, Single value (SLO burn).

## SPL

```spl
index=containers sourcetype="envoy:access"
| where like(gateway_workload, "istio-ingress%") OR like(kubernetes_pod_name, "istio-ingress%")
| eval dur_ms=tonumber(duration_ms)
| timechart span=5m perc95(dur_ms) as p95_ms, perc99(dur_ms) as p99_ms by route_name
```

## Visualization

Time chart (p95/p99 latency by route), Geographic or by-AZ breakdown if multi-region, Single value (SLO burn).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
