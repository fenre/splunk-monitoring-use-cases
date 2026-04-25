<!-- AUTO-GENERATED from UC-3.2.42.json — DO NOT EDIT -->

---
id: "3.2.42"
title: "Kubelet Certificate Rotation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.42 · Kubelet Certificate Rotation

## Description

Kubelet client/server cert expiry breaks node registration and pod lifecycle; tracking rotation events prevents surprise NotReady storms.

## Value

Kubelet client/server cert expiry breaks node registration and pod lifecycle; tracking rotation events prevents surprise NotReady storms.

## Implementation

Forward kubelet logs and optional script exporting kubelet cert `NotAfter`. Alert at 30/14 days for self-managed rotation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: kubelet logs, node cert exporter.
• Ensure the following data sources are available: `sourcetype=kube:kubelet`, `sourcetype=kube:node:cert`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward kubelet logs and optional script exporting kubelet cert `NotAfter`. Alert at 30/14 days for self-managed rotation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:node:cert" role="kubelet"
| eval days_left=round((not_after-now())/86400,0)
| where days_left<30
| table host role days_left
```

Understanding this SPL

**Kubelet Certificate Rotation** — Kubelet client/server cert expiry breaks node registration and pod lifecycle; tracking rotation events prevents surprise NotReady storms.

Documented **Data sources**: `sourcetype=kube:kubelet`, `sourcetype=kube:node:cert`. **App/TA** (typical add-on context): kubelet logs, node cert exporter. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:node:cert. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:node:cert". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **days_left** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_left<30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kubelet Certificate Rotation**): table host role days_left


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (node, days left), Timeline (rotation success), Single value (nodes expiring <30d).

## SPL

```spl
index=k8s sourcetype="kube:node:cert" role="kubelet"
| eval days_left=round((not_after-now())/86400,0)
| where days_left<30
| table host role days_left
```

## Visualization

Table (node, days left), Timeline (rotation success), Single value (nodes expiring <30d).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
