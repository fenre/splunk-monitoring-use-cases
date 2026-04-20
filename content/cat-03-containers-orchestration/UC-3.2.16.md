---
id: "3.2.16"
title: "Kubernetes PersistentVolume Claim Capacity"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.16 · Kubernetes PersistentVolume Claim Capacity

## Description

PVC approaching storage limits; prevents application failures from full volumes.

## Value

PVC approaching storage limits; prevents application failures from full volumes.

## Implementation

Configure Splunk Connect for Kubernetes or OTel Collector to scrape kubelet metrics. The kubelet exposes volume stats at `/metrics` on each node. Extract `kubelet_volume_stats_used_bytes` and `kubelet_volume_stats_capacity_bytes` with labels `namespace`, `persistentvolumeclaim`. Alert when any PVC exceeds 80% capacity. Consider 90% for critical stateful workloads.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes, metrics from kubelet.
• Ensure the following data sources are available: kubelet metrics (`kubelet_volume_stats_used_bytes`, `kubelet_volume_stats_capacity_bytes`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Splunk Connect for Kubernetes or OTel Collector to scrape kubelet metrics. The kubelet exposes volume stats at `/metrics` on each node. Extract `kubelet_volume_stats_used_bytes` and `kubelet_volume_stats_capacity_bytes` with labels `namespace`, `persistentvolumeclaim`. Alert when any PVC exceeds 80% capacity. Consider 90% for critical stateful workloads.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" (metric_name="kubelet_volume_stats_used_bytes" OR metric_name="kubelet_volume_stats_capacity_bytes")
| stats latest(_value) as value by metric_name, namespace, persistentvolumeclaim, node
| xyseries namespace,persistentvolumeclaim,node metric_name value
| eval used_pct = round(kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100, 1)
| where used_pct > 80
| table namespace persistentvolumeclaim node used_pct kubelet_volume_stats_used_bytes kubelet_volume_stats_capacity_bytes
| sort -used_pct
```

Understanding this SPL

**Kubernetes PersistentVolume Claim Capacity** — PVC approaching storage limits; prevents application failures from full volumes.

Documented **Data sources**: kubelet metrics (`kubelet_volume_stats_used_bytes`, `kubelet_volume_stats_capacity_bytes`). **App/TA** (typical add-on context): Splunk Connect for Kubernetes, metrics from kubelet. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by metric_name, namespace, persistentvolumeclaim, node** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pivots fields for charting with `xyseries`.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes PersistentVolume Claim Capacity**): table namespace persistentvolumeclaim node used_pct kubelet_volume_stats_used_bytes kubelet_volume_stats_capacity_bytes
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per PVC, Table (namespace, PVC, node, used %, bytes), Line chart (trend over time).

## SPL

```spl
index=k8s sourcetype="kube:metrics" (metric_name="kubelet_volume_stats_used_bytes" OR metric_name="kubelet_volume_stats_capacity_bytes")
| stats latest(_value) as value by metric_name, namespace, persistentvolumeclaim, node
| xyseries namespace,persistentvolumeclaim,node metric_name value
| eval used_pct = round(kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes * 100, 1)
| where used_pct > 80
| table namespace persistentvolumeclaim node used_pct kubelet_volume_stats_used_bytes kubelet_volume_stats_capacity_bytes
| sort -used_pct
```

## Visualization

Gauge per PVC, Table (namespace, PVC, node, used %, bytes), Line chart (trend over time).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
