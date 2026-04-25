<!-- AUTO-GENERATED from UC-3.3.7.json — DO NOT EDIT -->

---
id: "3.3.7"
title: "Build Config Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.3.7 · Build Config Failures

## Description

`BuildConfig` runs power S2I and Docker builds; failed builds block image promotion and rollouts tied to CI/CD.

## Value

`BuildConfig` runs power S2I and Docker builds; failed builds block image promotion and rollouts tied to CI/CD.

## Implementation

Ensure build events include `BuildConfig` correlation. Group by namespace and builder image. Alert on repeated failures for the same `BuildConfig` within 1 hour.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenShift event forwarding.
• Ensure the following data sources are available: `sourcetype=kube:objects:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure build events include `BuildConfig` correlation. Group by namespace and builder image. Alert on repeated failures for the same `BuildConfig` within 1 hour.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=openshift sourcetype="kube:objects:events" involvedObject.kind="Build" (reason="BuildFailed" OR reason="Error" OR reason="Failed")
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```

Understanding this SPL

**Build Config Failures** — `BuildConfig` runs power S2I and Docker builds; failed builds block image promotion and rollouts tied to CI/CD.

Documented **Data sources**: `sourcetype=kube:objects:events`. **App/TA** (typical add-on context): OpenShift event forwarding. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: openshift; **sourcetype**: kube:objects:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=openshift, sourcetype="kube:objects:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by namespace, involvedObject.name, reason, message** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (build, namespace, message), Line chart (failure rate), Bar chart by builder image.

## SPL

```spl
index=openshift sourcetype="kube:objects:events" involvedObject.kind="Build" (reason="BuildFailed" OR reason="Error" OR reason="Failed")
| stats count by namespace, involvedObject.name, reason, message
| sort -count
```

## Visualization

Table (build, namespace, message), Line chart (failure rate), Bar chart by builder image.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
