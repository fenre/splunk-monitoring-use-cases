<!-- AUTO-GENERATED from UC-3.2.30.json — DO NOT EDIT -->

---
id: "3.2.30"
title: "Init Container Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.2.30 · Init Container Failures

## Description

Failed inits block app containers entirely; fast detection shortens MTTR for migrations and secret-fetch steps.

## Value

Failed inits block app containers entirely; fast detection shortens MTTR for migrations and secret-fetch steps.

## Implementation

Forward events mentioning init containers; optionally ingest pod status subresource via exporter. Alert on non-zero init exit or ImagePull errors on init images.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Kubernetes events, container status JSON.
• Ensure the following data sources are available: `sourcetype=kube:objects:events`, `sourcetype=kube:container:meta`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward events mentioning init containers; optionally ingest pod status subresource via exporter. Alert on non-zero init exit or ImagePull errors on init images.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=k8s sourcetype="kube:container:meta" init="true"
| where exit_code!=0 OR state="waiting"
| table namespace pod_name container_name state exit_code
```

Understanding this SPL

**Init Container Failures** — Failed inits block app containers entirely; fast detection shortens MTTR for migrations and secret-fetch steps.

Documented **Data sources**: `sourcetype=kube:objects:events`, `sourcetype=kube:container:meta`. **App/TA** (typical add-on context): Kubernetes events, container status JSON. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: k8s; **sourcetype**: kube:container:meta. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=k8s, sourcetype="kube:container:meta". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where exit_code!=0 OR state="waiting"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Init Container Failures**): table namespace pod_name container_name state exit_code


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (pod, init container, reason), Timeline, Single value (failed inits/hour).

## SPL

```spl
index=k8s sourcetype="kube:container:meta" init="true"
| where exit_code!=0 OR state="waiting"
| table namespace pod_name container_name state exit_code
```

## Visualization

Table (pod, init container, reason), Timeline, Single value (failed inits/hour).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
