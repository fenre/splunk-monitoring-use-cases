<!-- AUTO-GENERATED from UC-3.2.10.json — DO NOT EDIT -->

---
id: "3.2.10"
title: "CrashLoopBackOff Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.2.10 · CrashLoopBackOff Detection

## Description

CrashLoopBackOff is the most common Kubernetes failure mode. The pod is crashing, restarting, and crashing again with exponential backoff. Service is down.

## Value

CrashLoopBackOff is the most common Kubernetes failure mode. The pod is crashing, restarting, and crashing again with exponential backoff. Service is down.

## Implementation

Monitor Kubernetes events for `BackOff` reason. Also check container status for `waiting.reason=CrashLoopBackOff`. Alert immediately. Include container logs in alert for diagnostic context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, kube-state-metrics.
• Ensure the following data sources are available: `sourcetype=kube:container:meta`, Kubernetes events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Kubernetes events for `BackOff` reason. Also check container status for `waiting.reason=CrashLoopBackOff`. Alert immediately. Include container logs in alert for diagnostic context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:events" reason="BackOff"
| stats count by namespace, involvedObject.name, message
| where count > 3
| sort -count
```

Understanding this SPL

**CrashLoopBackOff Detection** — CrashLoopBackOff is the most common Kubernetes failure mode. The pod is crashing, restarting, and crashing again with exponential backoff. Service is down.

Documented **Data sources**: `sourcetype=kube:container:meta`, Kubernetes events. **App/TA** (typical add-on context): Splunk OTel Collector, kube-state-metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:events. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pod, namespace, count, message), Status panel, Single value (CrashLoop pods count).

## SPL

```spl
index=k8s sourcetype="kube:events" reason="BackOff"
| stats count by namespace, involvedObject.name, message
| where count > 3
| sort -count
```

## Visualization

Table (pod, namespace, count, message), Status panel, Single value (CrashLoop pods count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
