---
id: "4.3.4"
title: "GKE Cluster Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.4 · GKE Cluster Health

## Description

GKE cluster health monitoring for managed Kubernetes in GCP. Node pools, upgrade status, and workload health.

## Value

GKE cluster health monitoring for managed Kubernetes in GCP. Node pools, upgrade status, and workload health.

## Implementation

GKE logs flow through Cloud Logging. Sink to Pub/Sub for Splunk ingestion. Deploy OTel Collector in GKE for K8s-native monitoring (see Category 3.2).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`, Splunk OTel Collector.
• Ensure the following data sources are available: GKE logs via Pub/Sub, Cloud Monitoring metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
GKE logs flow through Cloud Logging. Sink to Pub/Sub for Splunk ingestion. Deploy OTel Collector in GKE for K8s-native monitoring (see Category 3.2).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster"
| spath output=severity path=severity
| where severity="ERROR"
| stats count by resource.labels.cluster_name, textPayload
| sort -count
```

Understanding this SPL

**GKE Cluster Health** — GKE cluster health monitoring for managed Kubernetes in GCP. Node pools, upgrade status, and workload health.

Documented **Data sources**: GKE logs via Pub/Sub, Cloud Monitoring metrics. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`, Splunk OTel Collector. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where severity="ERROR"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by resource.labels.cluster_name, textPayload** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel, Error table, Timeline.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="k8s_cluster"
| spath output=severity path=severity
| where severity="ERROR"
| stats count by resource.labels.cluster_name, textPayload
| sort -count
```

## Visualization

Status panel, Error table, Timeline.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
