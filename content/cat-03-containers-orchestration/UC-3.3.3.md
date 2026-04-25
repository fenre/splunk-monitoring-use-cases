<!-- AUTO-GENERATED from UC-3.3.3.json — DO NOT EDIT -->

---
id: "3.3.3"
title: "Build Failure Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.3 · Build Failure Monitoring

## Description

OpenShift Source-to-Image (S2I) build failures block application deployments. Trend analysis reveals systemic build infrastructure issues.

## Value

OpenShift Source-to-Image (S2I) build failures block application deployments. Trend analysis reveals systemic build infrastructure issues.

## Implementation

Forward OpenShift events. Alert on BuildFailed events. Track build success/failure rate per namespace over time. Investigate common failure reasons (image pull, compile errors, push failures).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenShift event forwarding.
• Ensure the following data sources are available: `sourcetype=kube:events` (Build events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward OpenShift events. Alert on BuildFailed events. Track build success/failure rate per namespace over time. Investigate common failure reasons (image pull, compile errors, push failures).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="kube:events" involvedObject.kind="Build" reason="BuildFailed"
| stats count by namespace, involvedObject.name, message
| sort -count
```

Understanding this SPL

**Build Failure Monitoring** — OpenShift Source-to-Image (S2I) build failures block application deployments. Trend analysis reveals systemic build infrastructure issues.

Documented **Data sources**: `sourcetype=kube:events` (Build events). **App/TA** (typical add-on context): OpenShift event forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, message** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (build, namespace, reason), Line chart (success rate %), Bar chart by failure type.

## SPL

```spl
index=openshift sourcetype="kube:events" involvedObject.kind="Build" reason="BuildFailed"
| stats count by namespace, involvedObject.name, message
| sort -count
```

## Visualization

Table (build, namespace, reason), Line chart (success rate %), Bar chart by failure type.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
