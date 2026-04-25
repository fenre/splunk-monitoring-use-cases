<!-- AUTO-GENERATED from UC-3.2.25.json — DO NOT EDIT -->

---
id: "3.2.25"
title: "PV/PVC Capacity Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.25 · PV/PVC Capacity Monitoring

## Description

Proactive free-space visibility on bound PVs avoids read-only filesystems and database corruption across the cluster.

## Value

Proactive free-space visibility on bound PVs avoids read-only filesystems and database corruption across the cluster.

## Implementation

Scrape kubelet volume stats with PVC labels. Dashboard all namespaces; alert at 85%/95% tiers. Include storage class in lookup tables for business priority.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector (kubelet metrics).
• Ensure the following data sources are available: `sourcetype=kube:metrics`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape kubelet volume stats with PVC labels. Dashboard all namespaces; alert at 85%/95% tiers. Include storage class in lookup tables for business priority.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_used_bytes"
| stats latest(_value) as used by namespace, persistentvolumeclaim, node
| join type=left max=1 namespace persistentvolumeclaim node [
    search index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_capacity_bytes"
    | stats latest(_value) as cap by namespace, persistentvolumeclaim, node
]
| eval used_pct=if(cap>0, round(used/cap*100,1), null())
| where used_pct>85
| table namespace persistentvolumeclaim node used_pct used cap
| sort -used_pct
```

Understanding this SPL

**PV/PVC Capacity Monitoring** — Proactive free-space visibility on bound PVs avoids read-only filesystems and database corruption across the cluster.

Documented **Data sources**: `sourcetype=kube:metrics`. **App/TA** (typical add-on context): Splunk OTel Collector (kubelet metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, persistentvolumeclaim, node** so each row reflects one combination of those dimensions.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct>85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **PV/PVC Capacity Monitoring**): table namespace persistentvolumeclaim node used_pct used cap
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per PVC, Table (namespace, PVC, used %), Heatmap (node × PVC).

## SPL

```spl
index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_used_bytes"
| stats latest(_value) as used by namespace, persistentvolumeclaim, node
| join type=left max=1 namespace persistentvolumeclaim node [
    search index=k8s sourcetype="kube:metrics" metric_name="kubelet_volume_stats_capacity_bytes"
    | stats latest(_value) as cap by namespace, persistentvolumeclaim, node
]
| eval used_pct=if(cap>0, round(used/cap*100,1), null())
| where used_pct>85
| table namespace persistentvolumeclaim node used_pct used cap
| sort -used_pct
```

## Visualization

Gauge per PVC, Table (namespace, PVC, used %), Heatmap (node × PVC).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
