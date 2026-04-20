---
id: "4.5.8"
title: "GCP Cloud Functions Timeout Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.5.8 · GCP Cloud Functions Timeout Monitoring

## Description

Timeouts indicate hung dependencies or insufficient deadline; they drive retries, duplicate side effects, and user-visible failures in synchronous invocations.

## Value

Timeouts indicate hung dependencies or insufficient deadline; they drive retries, duplicate side effects, and user-visible failures in synchronous invocations.

## Implementation

Forward Cloud Functions logs to Pub/Sub and ingest with `resource.type="cloud_function"`. Optionally add monitoring metrics for execution times and error result codes. Alert on timeout string patterns or rising timeout counts after dependency or region incidents.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (Cloud Logging for `cloud_function`), `sourcetype=google:gcp:monitoring`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Cloud Functions logs to Pub/Sub and ingest with `resource.type="cloud_function"`. Optionally add monitoring metrics for execution times and error result codes. Alert on timeout string patterns or rising timeout counts after dependency or region incidents.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| where match(_raw, "(?i)timeout|deadline exceeded|function execution took too long")
| stats count as timeout_events by resource.labels.function_name, resource.labels.region
| sort -timeout_events
```

Understanding this SPL

**GCP Cloud Functions Timeout Monitoring** — Timeouts indicate hung dependencies or insufficient deadline; they drive retries, duplicate side effects, and user-visible failures in synchronous invocations.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (Cloud Logging for `cloud_function`), `sourcetype=google:gcp:monitoring`. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(_raw, "(?i)timeout|deadline exceeded|function execution took too long")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by resource.labels.function_name, resource.labels.region** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (timeouts by function), Line chart (timeouts over time), Table (function_name, region, count).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="cloud_function"
| where match(_raw, "(?i)timeout|deadline exceeded|function execution took too long")
| stats count as timeout_events by resource.labels.function_name, resource.labels.region
| sort -timeout_events
```

## Visualization

Column chart (timeouts by function), Line chart (timeouts over time), Table (function_name, region, count).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
