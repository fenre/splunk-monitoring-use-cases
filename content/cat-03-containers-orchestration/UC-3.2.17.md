---
id: "3.2.17"
title: "Kubernetes HorizontalPodAutoscaler Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.17 · Kubernetes HorizontalPodAutoscaler Status

## Description

HPA at max replicas, unable to scale, or flapping between min and max.

## Value

HPA at max replicas, unable to scale, or flapping between min and max.

## Implementation

Collect kube-state-metrics HPA series via Splunk Connect for Kubernetes. Alert when `current_replicas == max_replicas` (HPA cannot scale further; application may be under-provisioned). Also alert on rapid replica flapping (e.g. current oscillating between min and max within 10 minutes) indicating unstable scaling.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes.
• Ensure the following data sources are available: kube-state-metrics (`kube_horizontalpodautoscaler_status_current_replicas`, `kube_horizontalpodautoscaler_spec_min_replicas`, `kube_horizontalpodautoscaler_spec_max_replicas`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect kube-state-metrics HPA series via Splunk Connect for Kubernetes. Alert when `current_replicas == max_replicas` (HPA cannot scale further; application may be under-provisioned). Also alert on rapid replica flapping (e.g. current oscillating between min and max within 10 minutes) indicating unstable scaling.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_*"
| stats latest(_value) as value by metric_name, namespace, horizontalpodautoscaler
| eval current_replicas = case(metric_name="kube_horizontalpodautoscaler_status_current_replicas", value)
| eval min_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_min_replicas", value)
| eval max_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_max_replicas", value)
| stats max(current_replicas) as current_replicas, max(min_replicas) as min_replicas, max(max_replicas) as max_replicas by namespace, horizontalpodautoscaler
| eval at_max = if(current_replicas >= max_replicas AND max_replicas > 0, 1, 0)
| where at_max=1
| table namespace horizontalpodautoscaler current_replicas min_replicas max_replicas
| sort -current_replicas
```

Understanding this SPL

**Kubernetes HorizontalPodAutoscaler Status** — HPA at max replicas, unable to scale, or flapping between min and max.

Documented **Data sources**: kube-state-metrics (`kube_horizontalpodautoscaler_status_current_replicas`, `kube_horizontalpodautoscaler_spec_min_replicas`, `kube_horizontalpodautoscaler_spec_max_replicas`). **App/TA** (typical add-on context): Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by metric_name, namespace, horizontalpodautoscaler** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **current_replicas** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **min_replicas** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **max_replicas** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by namespace, horizontalpodautoscaler** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **at_max** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where at_max=1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes HorizontalPodAutoscaler Status**): table namespace horizontalpodautoscaler current_replicas min_replicas max_replicas
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (HPA, namespace, current, min, max), Status indicator (at max = warning), Line chart (replicas over time).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kube_horizontalpodautoscaler_*"
| stats latest(_value) as value by metric_name, namespace, horizontalpodautoscaler
| eval current_replicas = case(metric_name="kube_horizontalpodautoscaler_status_current_replicas", value)
| eval min_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_min_replicas", value)
| eval max_replicas = case(metric_name="kube_horizontalpodautoscaler_spec_max_replicas", value)
| stats max(current_replicas) as current_replicas, max(min_replicas) as min_replicas, max(max_replicas) as max_replicas by namespace, horizontalpodautoscaler
| eval at_max = if(current_replicas >= max_replicas AND max_replicas > 0, 1, 0)
| where at_max=1
| table namespace horizontalpodautoscaler current_replicas min_replicas max_replicas
| sort -current_replicas
```

## Visualization

Table (HPA, namespace, current, min, max), Status indicator (at max = warning), Line chart (replicas over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
