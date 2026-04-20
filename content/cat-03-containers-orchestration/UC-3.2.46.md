---
id: "3.2.46"
title: "Cluster Autoscaler Pending Pods"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.46 · Cluster Autoscaler Pending Pods

## Description

Cluster autoscaler unable to scale out leaves pods pending during traffic spikes; monitoring pending duration and CA logs protects scale-out SLAs.

## Value

Cluster autoscaler unable to scale out leaves pods pending during traffic spikes; monitoring pending duration and CA logs protects scale-out SLAs.

## Implementation

Forward cluster-autoscaler Deployment logs. Correlate `NotTriggeredScaleUp` with max node pool size and quotas. Alert when scheduling failures persist >5 minutes while CA reports scale blocked.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: cluster-autoscaler logs, Kubernetes events.
• Ensure the following data sources are available: `sourcetype=kube:cluster-autoscaler`, `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward cluster-autoscaler Deployment logs. Correlate `NotTriggeredScaleUp` with max node pool size and quotas. Alert when scheduling failures persist >5 minutes while CA reports scale blocked.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| eval age_sec=now()-_time
| where age_sec>300
| stats max(age_sec) as max_pending by namespace, involvedObject.name, message
| sort -max_pending
```

Understanding this SPL

**Cluster Autoscaler Pending Pods** — Cluster autoscaler unable to scale out leaves pods pending during traffic spikes; monitoring pending duration and CA logs protects scale-out SLAs.

Documented **Data sources**: `sourcetype=kube:cluster-autoscaler`, `sourcetype=kube:events`. **App/TA** (typical add-on context): cluster-autoscaler logs, Kubernetes events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **age_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where age_sec>300` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (reason, count), Timeline (scale-up), Single value (pending pods).

## SPL

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| eval age_sec=now()-_time
| where age_sec>300
| stats max(age_sec) as max_pending by namespace, involvedObject.name, message
| sort -max_pending
```

## Visualization

Table (reason, count), Timeline (scale-up), Single value (pending pods).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
