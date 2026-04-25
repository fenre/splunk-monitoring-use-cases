<!-- AUTO-GENERATED from UC-3.2.22.json — DO NOT EDIT -->

---
id: "3.2.22"
title: "Pod Security Admission Violations"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.2.22 · Pod Security Admission Violations

## Description

PSA denials block risky pods at admission; tracking them exposes misconfigured workloads and policy gaps before they reach production namespaces.

## Value

PSA denials block risky pods at admission; tracking them exposes misconfigured workloads and policy gaps before they reach production namespaces.

## Implementation

Enable audit policy capturing Pod create/update denials. Parse PSA-specific messages. Alert on spikes in a namespace or repeated denials for the same workload pattern.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes audit log forwarding.
• Ensure the following data sources are available: `sourcetype=kube:audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable audit policy capturing Pod create/update denials. Parse PSA-specific messages. Alert on spikes in a namespace or repeated denials for the same workload pattern.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:audit" objectRef.resource="pods"
| search "PodSecurity" OR "pod-security.kubernetes.io" OR "denied the request"
| stats count by user.username, objectRef.namespace, objectRef.name, responseStatus.reason
| sort -count
```

Understanding this SPL

**Pod Security Admission Violations** — PSA denials block risky pods at admission; tracking them exposes misconfigured workloads and policy gaps before they reach production namespaces.

Documented **Data sources**: `sourcetype=kube:audit`. **App/TA** (typical add-on context): Kubernetes audit log forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by user.username, objectRef.namespace, objectRef.name, responseStatus.reason** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (namespace, user, count), Bar chart by namespace, Timeline.

## SPL

```spl
index=k8s sourcetype="kube:audit" objectRef.resource="pods"
| search "PodSecurity" OR "pod-security.kubernetes.io" OR "denied the request"
| stats count by user.username, objectRef.namespace, objectRef.name, responseStatus.reason
| sort -count
```

## Visualization

Table (namespace, user, count), Bar chart by namespace, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
