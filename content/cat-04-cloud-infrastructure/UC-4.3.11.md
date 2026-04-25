<!-- AUTO-GENERATED from UC-4.3.11.json — DO NOT EDIT -->

---
id: "4.3.11"
title: "Cloud Storage (GCS) Request Metrics and Cost"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.3.11 · Cloud Storage (GCS) Request Metrics and Cost

## Description

GCS request count and latency support performance tuning. Cost tracking by bucket/class prevents bill shock.

## Value

GCS request count and latency support performance tuning. Cost tracking by bucket/class prevents bill shock.

## Implementation

Enable GCS request logging to Cloud Logging; sink to Pub/Sub for Splunk. Collect storage metrics. Ingest billing export for cost by bucket. Alert on anomalous request volume or cost spike.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring (storage.googleapis.com/request_count), Billing export.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable GCS request logging to Cloud Logging; sink to Pub/Sub for Splunk. Collect storage metrics. Ingest billing export for cost by bucket. Alert on anomalous request volume or cost spike.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.bucket_name
| sort -count
```

Understanding this SPL

**Cloud Storage (GCS) Request Metrics and Cost** — GCS request count and latency support performance tuning. Cost tracking by bucket/class prevents bill shock.

Documented **Data sources**: Cloud Monitoring (storage.googleapis.com/request_count), Billing export. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by method resource.labels.bucket_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (requests, cost by bucket), Table (bucket, method, count), Bar chart (cost by bucket).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" protoPayload.serviceName="storage.googleapis.com"
| spath output=method path=protoPayload.methodName
| stats count by method resource.labels.bucket_name
| sort -count
```

## Visualization

Line chart (requests, cost by bucket), Table (bucket, method, count), Bar chart (cost by bucket).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
