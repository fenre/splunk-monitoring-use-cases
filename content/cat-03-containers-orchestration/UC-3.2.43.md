---
id: "3.2.43"
title: "Container Probe Failure Analysis"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.43 · Container Probe Failure Analysis

## Description

Repeated readiness/liveness probe failures indicate dependency outages or mis-tuned thresholds before user-visible errors dominate.

## Value

Repeated readiness/liveness probe failures indicate dependency outages or mis-tuned thresholds before user-visible errors dominate.

## Implementation

Collect kubelet probe log lines. Bucket by container. Alert on sustained probe failure rate after deployments.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kubelet logs, Kubernetes events.
• Ensure the following data sources are available: `sourcetype=kube:kubelet`, `sourcetype=kube:objects:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect kubelet probe log lines. Bucket by container. Alert on sustained probe failure rate after deployments.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:objects:events" reason="Unhealthy"
| stats count by namespace, involvedObject.name, message
```

Understanding this SPL

**Container Probe Failure Analysis** — Repeated readiness/liveness probe failures indicate dependency outages or mis-tuned thresholds before user-visible errors dominate.

Documented **Data sources**: `sourcetype=kube:kubelet`, `sourcetype=kube:objects:events`. **App/TA** (typical add-on context): kubelet logs, Kubernetes events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:objects:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:objects:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pod, container, count), Timeline, Bar chart by workload.

## SPL

```spl
index=k8s sourcetype="kube:objects:events" reason="Unhealthy"
| stats count by namespace, involvedObject.name, message
```

## Visualization

Table (pod, container, count), Timeline, Bar chart by workload.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
