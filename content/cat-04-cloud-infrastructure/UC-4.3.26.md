<!-- AUTO-GENERATED from UC-4.3.26.json — DO NOT EDIT -->

---
id: "4.3.26"
title: "GKE Autopilot Pod Scaling"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.26 · GKE Autopilot Pod Scaling

## Description

Autopilot scales node pools automatically; failed scale-outs leave pods pending and degrade SLOs.

## Value

Autopilot scales node pools automatically; failed scale-outs leave pods pending and degrade SLOs.

## Implementation

Enable GKE logging and filter for scheduling events. Correlate with pending pod metrics if exported. Alert on rising pending pod count or repeated scale failures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (GKE cluster logs), `sourcetype=google:gcp:monitoring` (scheduler, pending pods).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable GKE logging and filter for scheduling events. Correlate with pending pod metrics if exported. Alert on rising pending pod count or repeated scale failures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" ("FailedScheduling" OR "Insufficient cpu" OR "Insufficient memory")
| stats count by resource.labels.cluster_name, jsonPayload.reason
| sort -count
```

Understanding this SPL

**GKE Autopilot Pod Scaling** — Autopilot scales node pools automatically; failed scale-outs leave pods pending and degrade SLOs.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (GKE cluster logs), `sourcetype=google:gcp:monitoring` (scheduler, pending pods). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.cluster_name, jsonPayload.reason** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (scheduling failures), Table (cluster, reason, count), Line chart (pending pods).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster" ("FailedScheduling" OR "Insufficient cpu" OR "Insufficient memory")
| stats count by resource.labels.cluster_name, jsonPayload.reason
| sort -count
```

## Visualization

Timeline (scheduling failures), Table (cluster, reason, count), Line chart (pending pods).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
