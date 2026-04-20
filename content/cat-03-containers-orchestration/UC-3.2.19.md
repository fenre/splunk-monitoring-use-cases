---
id: "3.2.19"
title: "Kubernetes DaemonSet Missing Pods"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.19 · Kubernetes DaemonSet Missing Pods

## Description

DaemonSet pods not running on all expected nodes.

## Value

DaemonSet pods not running on all expected nodes.

## Implementation

kube-state-metrics exposes DaemonSet status. Splunk Connect for Kubernetes collects this. Alert when `currentNumberScheduled < desiredNumberScheduled` (pods not scheduled) or `numberReady < desiredNumberScheduled` (pods scheduled but not ready). Critical for CNI, kube-proxy, and monitoring DaemonSets. Investigate node taints, resource constraints, or image pull issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes.
• Ensure the following data sources are available: kube-state-metrics (`kube_daemonset_status_desired_number_scheduled`, `kube_daemonset_status_current_number_scheduled`, `kube_daemonset_status_number_ready`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
kube-state-metrics exposes DaemonSet status. Splunk Connect for Kubernetes collects this. Alert when `currentNumberScheduled < desiredNumberScheduled` (pods not scheduled) or `numberReady < desiredNumberScheduled` (pods scheduled but not ready). Critical for CNI, kube-proxy, and monitoring DaemonSets. Investigate node taints, resource constraints, or image pull issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing_scheduled = desiredNumberScheduled - currentNumberScheduled
| eval missing_ready = desiredNumberScheduled - numberReady
| where missing_scheduled > 0 OR missing_ready > 0
| table namespace daemonset_name desiredNumberScheduled currentNumberScheduled numberReady missing_scheduled missing_ready
| sort -missing_ready
```

Understanding this SPL

**Kubernetes DaemonSet Missing Pods** — DaemonSet pods not running on all expected nodes.

Documented **Data sources**: kube-state-metrics (`kube_daemonset_status_desired_number_scheduled`, `kube_daemonset_status_current_number_scheduled`, `kube_daemonset_status_number_ready`). **App/TA** (typical add-on context): Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:daemonset:meta. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:daemonset:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **missing_scheduled** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **missing_ready** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where missing_scheduled > 0 OR missing_ready > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubernetes DaemonSet Missing Pods**): table namespace daemonset_name desiredNumberScheduled currentNumberScheduled numberReady missing_scheduled missing_ready
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DaemonSet, desired, scheduled, ready, missing), Status grid by DaemonSet, Single value (DaemonSets with gaps).

## SPL

```spl
index=k8s sourcetype="kube:daemonset:meta"
| eval missing_scheduled = desiredNumberScheduled - currentNumberScheduled
| eval missing_ready = desiredNumberScheduled - numberReady
| where missing_scheduled > 0 OR missing_ready > 0
| table namespace daemonset_name desiredNumberScheduled currentNumberScheduled numberReady missing_scheduled missing_ready
| sort -missing_ready
```

## Visualization

Table (DaemonSet, desired, scheduled, ready, missing), Status grid by DaemonSet, Single value (DaemonSets with gaps).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
