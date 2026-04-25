<!-- AUTO-GENERATED from UC-3.2.36.json — DO NOT EDIT -->

---
id: "3.2.36"
title: "Namespace Resource Limit Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.36 · Namespace Resource Limit Enforcement

## Description

`LimitRange` defaults and max per-container caps prevent one pod from consuming a whole namespace budget; violations indicate chart misconfigurations.

## Value

`LimitRange` defaults and max per-container caps prevent one pod from consuming a whole namespace budget; violations indicate chart misconfigurations.

## Implementation

Track events when requests exceed LimitRange. Use audit 422 responses. Dashboard per namespace against documented standards.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes events, admission audit.
• Ensure the following data sources are available: `sourcetype=kube:objects:events`, `sourcetype=kube:audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Track events when requests exceed LimitRange. Use audit 422 responses. Dashboard per namespace against documented standards.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:audit" objectRef.resource="pods" responseStatus.code=422
| stats count by objectRef.namespace, user.username
```

Understanding this SPL

**Namespace Resource Limit Enforcement** — `LimitRange` defaults and max per-container caps prevent one pod from consuming a whole namespace budget; violations indicate chart misconfigurations.

Documented **Data sources**: `sourcetype=kube:objects:events`, `sourcetype=kube:audit`. **App/TA** (typical add-on context): Kubernetes events, admission audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by objectRef.namespace, user.username** so each row reflects one combination of those dimensions.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, workload, reason), Timeline, Single value (limit violations/day).

## SPL

```spl
index=k8s sourcetype="kube:audit" objectRef.resource="pods" responseStatus.code=422
| stats count by objectRef.namespace, user.username
```

## Visualization

Table (namespace, workload, reason), Timeline, Single value (limit violations/day).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
