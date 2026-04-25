<!-- AUTO-GENERATED from UC-3.2.15.json — DO NOT EDIT -->

---
id: "3.2.15"
title: "DaemonSet Completeness"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.2.15 · DaemonSet Completeness

## Description

DaemonSets (monitoring agents, log forwarders, network plugins) must run on every eligible node. Missing instances create monitoring or networking gaps.

## Value

DaemonSets (monitoring agents, log forwarders, network plugins) must run on every eligible node. Missing instances create monitoring or networking gaps.

## Implementation

kube-state-metrics reports DaemonSet status. Alert when `numberReady < desiredNumberScheduled` for >5 minutes. Critical for infrastructure DaemonSets (CNI plugins, OTel Collector, kube-proxy).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:daemonset:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
kube-state-metrics reports DaemonSet status. Alert when `numberReady < desiredNumberScheduled` for >5 minutes. Critical for infrastructure DaemonSets (CNI plugins, OTel Collector, kube-proxy).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing = desiredNumberScheduled - numberReady
| where missing > 0
| table namespace daemonset_name desiredNumberScheduled numberReady missing
```

Understanding this SPL

**DaemonSet Completeness** — DaemonSets (monitoring agents, log forwarders, network plugins) must run on every eligible node. Missing instances create monitoring or networking gaps.

Documented **Data sources**: `sourcetype=kube:daemonset:meta`. **App/TA** (typical add-on context): Splunk OTel Collector, kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:daemonset:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:daemonset:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **missing** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where missing > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **DaemonSet Completeness**): table namespace daemonset_name desiredNumberScheduled numberReady missing


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DaemonSet, desired, ready, missing), Status indicator, Single value.

## SPL

```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing = desiredNumberScheduled - numberReady
| where missing > 0
| table namespace daemonset_name desiredNumberScheduled numberReady missing
```

## Visualization

Table (DaemonSet, desired, ready, missing), Status indicator, Single value.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
