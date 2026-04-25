<!-- AUTO-GENERATED from UC-3.3.4.json — DO NOT EDIT -->

---
id: "3.3.4"
title: "SCC Violation Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.3.4 · SCC Violation Detection

## Description

Security Context Constraint violations mean pods are attempting to run with permissions beyond their allowed scope. Could indicate misconfiguration or an attack.

## Value

Security Context Constraint violations mean pods are attempting to run with permissions beyond their allowed scope. Could indicate misconfiguration or an attack.

## Implementation

Enable and forward OpenShift audit logs. Alert on SCC-related 403 errors. Track which SCCs are most commonly requested and denied.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenShift audit log forwarding.
• Ensure the following data sources are available: `sourcetype=openshift:audit`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable and forward OpenShift audit logs. Alert on SCC-related 403 errors. Track which SCCs are most commonly requested and denied.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="openshift:audit" responseStatus.code=403 objectRef.resource="pods"
| search "unable to validate against any security context constraint"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```

Understanding this SPL

**SCC Violation Detection** — Security Context Constraint violations mean pods are attempting to run with permissions beyond their allowed scope. Could indicate misconfiguration or an attack.

Documented **Data sources**: `sourcetype=openshift:audit`. **App/TA** (typical add-on context): OpenShift audit log forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: openshift:audit. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="openshift:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by user.username, objectRef.namespace, objectRef.name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, namespace, pod, SCC requested), Bar chart by SCC, Timeline.

## SPL

```spl
index=openshift sourcetype="openshift:audit" responseStatus.code=403 objectRef.resource="pods"
| search "unable to validate against any security context constraint"
| stats count by user.username, objectRef.namespace, objectRef.name
| sort -count
```

## Visualization

Table (user, namespace, pod, SCC requested), Bar chart by SCC, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
