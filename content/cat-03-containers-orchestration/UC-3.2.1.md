---
id: "3.2.1"
title: "Pod Restart Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.1 · Pod Restart Rate

## Description

High restart counts indicate application instability. Pods may appear "Running" but are constantly crashing and restarting, degrading service quality.

## Value

High restart counts indicate application instability. Pods may appear "Running" but are constantly crashing and restarting, degrading service quality.

## Implementation

Deploy the Splunk OTel Collector as a DaemonSet for kube-state-metrics. The restart counter (`kube_pod_container_status_restarts_total`) is cumulative, so use a windowed increase (`streamstats` delta or `mstats` rate) rather than raw max. Alert when the 1-hour increase exceeds 5 for any pod outside `kube-system`. Filter known CronJob namespaces with a lookup to reduce noise.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OpenTelemetry Collector for K8s.
• Ensure the following data sources are available: `sourcetype=kube:container:meta`, kube-state-metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy the Splunk OTel Collector as a DaemonSet for kube-state-metrics. The restart counter (`kube_pod_container_status_restarts_total`) is cumulative, so use a windowed increase (`streamstats` delta or `mstats` rate) rather than raw max. Alert when the 1-hour increase exceeds 5 for any pod outside `kube-system`. Filter known CronJob namespaces with a lookup to reduce noise.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:container:meta"
| stats max(restartCount) as restarts by namespace, pod_name, container_name
| where restarts > 5
| sort -restarts
```

Understanding this SPL

**Pod Restart Rate** — High restart counts indicate application instability. Pods may appear "Running" but are constantly crashing and restarting, degrading service quality.

Documented **Data sources**: `sourcetype=kube:container:meta`, kube-state-metrics. **App/TA** (typical add-on context): Splunk OpenTelemetry Collector for K8s. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:container:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:container:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, pod_name, container_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where restarts > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, pod, container, restarts), Bar chart by namespace, Trending line.

## SPL

```spl
index=k8s sourcetype="kube:container:meta"
| stats max(restartCount) as restarts by namespace, pod_name, container_name
| where restarts > 5
| sort -restarts
```

## Visualization

Table (namespace, pod, container, restarts), Bar chart by namespace, Trending line.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
