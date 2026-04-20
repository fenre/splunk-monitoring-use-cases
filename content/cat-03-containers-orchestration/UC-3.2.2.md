---
id: "3.2.2"
title: "Pod Scheduling Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.2 · Pod Scheduling Failures

## Description

Pods stuck in Pending can't serve traffic. Usually caused by insufficient CPU/memory, node affinity rules, or persistent volume claim issues.

## Value

Pods stuck in Pending can't serve traffic. Usually caused by insufficient CPU/memory, node affinity rules, or persistent volume claim issues.

## Implementation

Forward Kubernetes events to Splunk. Alert on FailedScheduling events persisting >5 minutes. Parse the event message for the specific cause (Insufficient cpu, node affinity, PVC not bound, etc.).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, Kubernetes event forwarding.
• Ensure the following data sources are available: `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Kubernetes events to Splunk. Alert on FailedScheduling events persisting >5 minutes. Parse the event message for the specific cause (Insufficient cpu, node affinity, PVC not bound, etc.).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| stats count by namespace, involvedObject.name, message
| sort -count
```

Understanding this SPL

**Pod Scheduling Failures** — Pods stuck in Pending can't serve traffic. Usually caused by insufficient CPU/memory, node affinity rules, or persistent volume claim issues.

Documented **Data sources**: `sourcetype=kube:events`. **App/TA** (typical add-on context): Splunk OTel Collector, Kubernetes event forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pod, namespace, reason), Single value (pending pods), Timeline.

## SPL

```spl
index=k8s sourcetype="kube:events" reason="FailedScheduling"
| stats count by namespace, involvedObject.name, message
| sort -count
```

## Visualization

Table (pod, namespace, reason), Single value (pending pods), Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
