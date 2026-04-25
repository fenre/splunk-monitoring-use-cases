<!-- AUTO-GENERATED from UC-4.3.8.json — DO NOT EDIT -->

---
id: "4.3.8"
title: "Cloud Run/Functions Errors"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.3.8 · Cloud Run/Functions Errors

## Description

Serverless function errors and cold starts impact application reliability and user experience.

## Value

Serverless function errors and cold starts impact application reliability and user experience.

## Implementation

Forward Cloud Run/Functions logs via Pub/Sub. Monitor error rates, execution duration, and cold start frequency. Alert on error rate >5%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Run/Functions logs via Cloud Logging.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Cloud Run/Functions logs via Pub/Sub. Monitor error rates, execution duration, and cold start frequency. Alert on error rate >5%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function" severity="ERROR"
| spath output=function path=resource.labels.function_name
| stats count by function, textPayload
| sort -count
```

Understanding this SPL

**Cloud Run/Functions Errors** — Serverless function errors and cold starts impact application reliability and user experience.

Documented **Data sources**: Cloud Run/Functions logs via Cloud Logging. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by function, textPayload** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (errors over time), Bar chart (top error functions), Single value.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function" severity="ERROR"
| spath output=function path=resource.labels.function_name
| stats count by function, textPayload
| sort -count
```

## Visualization

Line chart (errors over time), Bar chart (top error functions), Single value.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
