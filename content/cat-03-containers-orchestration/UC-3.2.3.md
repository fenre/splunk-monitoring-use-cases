<!-- AUTO-GENERATED from UC-3.2.3.json — DO NOT EDIT -->

---
id: "3.2.3"
title: "Node NotReady Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.3 · Node NotReady Detection

## Description

A NotReady node can't run pods. Existing pods are evicted after the toleration timeout (default 5 min). Causes service disruption if no replacement capacity.

## Value

A NotReady node can't run pods. Existing pods are evicted after the toleration timeout (default 5 min). Causes service disruption if no replacement capacity.

## Implementation

OTel Collector monitors node conditions. Alert immediately on any node transitioning to NotReady. Correlate with kubelet logs on the affected node for root cause (disk pressure, memory pressure, PID pressure, network).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:node:meta`, Kubernetes events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
OTel Collector monitors node conditions. Alert immediately on any node transitioning to NotReady. Correlate with kubelet logs on the affected node for root cause (disk pressure, memory pressure, PID pressure, network).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:node:meta"
| where condition_ready="False"
| table _time node condition_ready
```

Understanding this SPL

**Node NotReady Detection** — A NotReady node can't run pods. Existing pods are evicted after the toleration timeout (default 5 min). Causes service disruption if no replacement capacity.

Documented **Data sources**: `sourcetype=kube:node:meta`, Kubernetes events. **App/TA** (typical add-on context): Splunk OTel Collector, kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:node:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:node:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where condition_ready="False"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Node NotReady Detection**): table _time node condition_ready


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Node status grid (green/red), Events timeline, Table.

## SPL

```spl
index=k8s sourcetype="kube:node:meta"
| where condition_ready="False"
| table _time node condition_ready
```

## Visualization

Node status grid (green/red), Events timeline, Table.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
