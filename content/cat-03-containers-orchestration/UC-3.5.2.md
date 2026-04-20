---
id: "3.5.2"
title: "Sidecar Proxy Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.5.2 · Sidecar Proxy Health

## Description

Unhealthy Envoy sidecars drop or misroute traffic; catching not-ready or crash-looping proxies avoids cascading failures across the mesh.

## Value

Unhealthy Envoy sidecars drop or misroute traffic; catching not-ready or crash-looping proxies avoids cascading failures across the mesh.

## Implementation

Ingest pod/container metrics from Prometheus or OTel Kubernetes receiver so `istio-proxy` containers expose readiness and restart counts. Correlate with kube-state-metrics `kube_pod_container_status_restarts_total` where available. Alert when sidecars are not ready or restart churn exceeds threshold after mesh upgrades.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (kubelet/cAdvisor or Prometheus kube-state-metrics), Kubernetes metadata.
• Ensure the following data sources are available: `sourcetype=kube:metrics` or `sourcetype=otel:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest pod/container metrics from Prometheus or OTel Kubernetes receiver so `istio-proxy` containers expose readiness and restart counts. Correlate with kube-state-metrics `kube_pod_container_status_restarts_total` where available. Alert when sidecars are not ready or restart churn exceeds threshold after mesh upgrades.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers (sourcetype="kube:metrics" OR sourcetype="otel:metrics")
| where match(pod, ".*-istio-proxy$") OR container_name="istio-proxy"
| stats latest(ready) as ready, latest(restarts) as restarts, latest(phase) as phase by pod, namespace, node
| where ready=0 OR restarts>3 OR phase!="Running"
| sort namespace, pod
```

Understanding this SPL

**Sidecar Proxy Health** — Unhealthy Envoy sidecars drop or misroute traffic; catching not-ready or crash-looping proxies avoids cascading failures across the mesh.

Documented **Data sources**: `sourcetype=kube:metrics` or `sourcetype=otel:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector (kubelet/cAdvisor or Prometheus kube-state-metrics), Kubernetes metadata. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: kube:metrics, otel:metrics. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(pod, ".*-istio-proxy$") OR container_name="istio-proxy"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by pod, namespace, node** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where ready=0 OR restarts>3 OR phase!="Running"` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, pod, ready, restarts), Timeline (restarts), Single value (unhealthy sidecar count).

## SPL

```spl
index=containers (sourcetype="kube:metrics" OR sourcetype="otel:metrics")
| where match(pod, ".*-istio-proxy$") OR container_name="istio-proxy"
| stats latest(ready) as ready, latest(restarts) as restarts, latest(phase) as phase by pod, namespace, node
| where ready=0 OR restarts>3 OR phase!="Running"
| sort namespace, pod
```

## Visualization

Table (namespace, pod, ready, restarts), Timeline (restarts), Single value (unhealthy sidecar count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
