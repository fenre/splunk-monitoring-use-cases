<!-- AUTO-GENERATED from UC-3.2.5.json — DO NOT EDIT -->

---
id: "3.2.5"
title: "Persistent Volume Claims"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.5 · Persistent Volume Claims

## Description

Unbound PVCs prevent stateful workloads (databases, message queues) from starting. Often caused by storage class misconfiguration or capacity.

## Value

Unbound PVCs prevent stateful workloads (databases, message queues) from starting. Often caused by storage class misconfiguration or capacity.

## Implementation

Forward Kubernetes events and PVC metadata. Alert on PVCs in Pending phase >5 minutes. Include storage class and requested size in alert context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk OTel Collector, Kubernetes events.
• Ensure the following data sources are available: `sourcetype=kube:events`, `sourcetype=kube:pvc:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Kubernetes events and PVC metadata. Alert on PVCs in Pending phase >5 minutes. Include storage class and requested size in alert context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:events" reason="ProvisioningFailed" OR reason="FailedBinding"
| stats count by namespace, involvedObject.name, message
| sort -count
```

Understanding this SPL

**Persistent Volume Claims** — Unbound PVCs prevent stateful workloads (databases, message queues) from starting. Often caused by storage class misconfiguration or capacity.

Documented **Data sources**: `sourcetype=kube:events`, `sourcetype=kube:pvc:meta`. **App/TA** (typical add-on context): Splunk OTel Collector, Kubernetes events. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (PVC, namespace, status, storage class), Status indicators.

## SPL

```spl
index=k8s sourcetype="kube:events" reason="ProvisioningFailed" OR reason="FailedBinding"
| stats count by namespace, involvedObject.name, message
| sort -count
```

## Visualization

Table (PVC, namespace, status, storage class), Status indicators.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
