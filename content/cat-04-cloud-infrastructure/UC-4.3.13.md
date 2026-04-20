---
id: "4.3.13"
title: "Cloud Build Build Failures and Duration"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.3.13 · Cloud Build Build Failures and Duration

## Description

Build failures block deployments. Duration trends support pipeline optimization and quota management.

## Value

Build failures block deployments. Duration trends support pipeline optimization and quota management.

## Implementation

Sink Cloud Build logs to Pub/Sub; ingest in Splunk. Alert when status=FAILURE or TIMEOUT. Track build duration and success rate by trigger. Correlate with source repo and branch.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Build logs via Pub/Sub (build completion events).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sink Cloud Build logs to Pub/Sub; ingest in Splunk. Alert when status=FAILURE or TIMEOUT. Track build duration and success rate by trigger. Correlate with source repo and branch.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="build" status="FAILURE"
| table _time buildId triggerId status message
| sort -_time
```

Understanding this SPL

**Cloud Build Build Failures and Duration** — Build failures block deployments. Duration trends support pipeline optimization and quota management.

Documented **Data sources**: Cloud Build logs via Pub/Sub (build completion events). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:pubsub:message. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:pubsub:message". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cloud Build Build Failures and Duration**): table _time buildId triggerId status message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (builds, failures by trigger), Table (build, trigger, status, duration), Single value (failure rate).

## SPL

```spl
index=gcp sourcetype="google:gcp:pubsub:message" resource.type="build" status="FAILURE"
| table _time buildId triggerId status message
| sort -_time
```

## Visualization

Line chart (builds, failures by trigger), Table (build, trigger, status, duration), Single value (failure rate).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
