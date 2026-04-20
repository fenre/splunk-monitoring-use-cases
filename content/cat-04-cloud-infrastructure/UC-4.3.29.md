---
id: "4.3.29"
title: "Pub/Sub Subscription Backlog"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.3.29 · Pub/Sub Subscription Backlog

## Description

Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

## Value

Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

## Implementation

Set per-subscription SLOs for max backlog and oldest age. Scale push subscribers or fix poison messages. Use dead-letter topics for bad payloads.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_google-cloudplatform`.
• Ensure the following data sources are available: `sourcetype=google:gcp:monitoring` (`pubsub.googleapis.com/subscription/num_undelivered_messages`, `oldest_unacked_message_age`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set per-subscription SLOs for max backlog and oldest age. Scale push subscribers or fix poison messages. Use dead-letter topics for bad payloads.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| stats latest(value) as backlog by resource.labels.subscription_id, bin(_time, 5m)
| where backlog > 10000
| sort - backlog
```

Understanding this SPL

**Pub/Sub Subscription Backlog** — Growing backlog signals consumer lag or under-provisioned workers; oldest-unacked age breaches processing SLAs.

Documented **Data sources**: `sourcetype=google:gcp:monitoring` (`pubsub.googleapis.com/subscription/num_undelivered_messages`, `oldest_unacked_message_age`). **App/TA** (typical add-on context): `Splunk_TA_google-cloudplatform`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gcp; **sourcetype**: google:gcp:monitoring. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=gcp, sourcetype="google:gcp:monitoring". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by resource.labels.subscription_id, bin(_time, 5m)** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where backlog > 10000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backlog over time), Single value (oldest message age), Table (subscription, backlog).

## SPL

```spl
index=gcp sourcetype="google:gcp:monitoring" metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"
| stats latest(value) as backlog by resource.labels.subscription_id, bin(_time, 5m)
| where backlog > 10000
| sort - backlog
```

## Visualization

Line chart (backlog over time), Single value (oldest message age), Table (subscription, backlog).

## References

- [Splunk_TA_google-cloudplatform](https://splunkbase.splunk.com/app/3088)
