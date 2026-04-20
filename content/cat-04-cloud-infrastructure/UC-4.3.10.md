---
id: "4.3.10"
title: "Cloud Pub/Sub Subscription Backlog and Dead Letter"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.10 · Cloud Pub/Sub Subscription Backlog and Dead Letter

## Description

Backlog (unacked messages) and dead-letter count indicate consumers falling behind or failing. Prevents message loss and SLA breach.

## Value

Backlog (unacked messages) and dead-letter count indicate consumers falling behind or failing. Prevents message loss and SLA breach.

## Implementation

Collect Pub/Sub subscription metrics. Alert when num_undelivered_messages exceeds threshold or dead_letter_message_count > 0. Monitor old_unacked_message_age for consumer lag.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: Cloud Monitoring (pubsub.googleapis.com/subscription/num_undelivered_messages, dead_letter_message_count).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Pub/Sub subscription metrics. Alert when num_undelivered_messages exceeds threshold or dead_letter_message_count > 0. Monitor old_unacked_message_age for consumer lag.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| where value > 1000
| timechart span=5m avg(value) by resource.labels.subscription_id
```

Understanding this SPL

**Cloud Pub/Sub Subscription Backlog and Dead Letter** — Backlog (unacked messages) and dead-letter count indicate consumers falling behind or failing. Prevents message loss and SLA breach.

Documented **Data sources**: Cloud Monitoring (pubsub.googleapis.com/subscription/num_undelivered_messages, dead_letter_message_count). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where value > 1000` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by resource.labels.subscription_id** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backlog, dead letter by subscription), Table (subscription, backlog), Single value (max backlog).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| where value > 1000
| timechart span=5m avg(value) by resource.labels.subscription_id
```

## Visualization

Line chart (backlog, dead letter by subscription), Table (subscription, backlog), Single value (max backlog).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
