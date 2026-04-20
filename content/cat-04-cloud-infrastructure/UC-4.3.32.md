---
id: "4.3.32"
title: "Cloud Logging Sink Health"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.32 · Cloud Logging Sink Health

## Description

Broken sinks drop audit and security logs silently; monitoring export errors preserves compliance and detection coverage.

## Value

Broken sinks drop audit and security logs silently; monitoring export errors preserves compliance and detection coverage.

## Implementation

Enable log metrics on sink write errors to Pub/Sub destinations. Alert on any error count > 0 in 15 minutes. Verify Pub/Sub IAM and destination bucket permissions after changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:pubsub:message` (logging sink errors), Admin Activity for sink changes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable log metrics on sink write errors to Pub/Sub destinations. Alert on any error count > 0 in 15 minutes. Verify Pub/Sub IAM and destination bucket permissions after changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*logging*" (severity="ERROR" OR "SinkDisappeared" OR "WriteError")
| stats count by resource.labels.project_id, textPayload
| sort -count
```

Understanding this SPL

**Cloud Logging Sink Health** — Broken sinks drop audit and security logs silently; monitoring export errors preserves compliance and detection coverage.

Documented **Data sources**: `sourcetype=google:gcp:pubsub:message` (logging sink errors), Admin Activity for sink changes. **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.project_id, textPayload** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (sink errors), Table (project, error text), Timeline.

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" logName="*logging*" (severity="ERROR" OR "SinkDisappeared" OR "WriteError")
| stats count by resource.labels.project_id, textPayload
| sort -count
```

## Visualization

Single value (sink errors), Table (project, error text), Timeline.

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
