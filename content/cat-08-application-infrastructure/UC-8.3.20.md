---
id: "8.3.20"
title: "NATS JetStream Consumer Ack Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.20 · NATS JetStream Consumer Ack Lag

## Description

`NumAckPending`, `NumRedelivered`, and consumer lag for JetStream streams indicate slow consumers or poison messages.

## Value

`NumAckPending`, `NumRedelivered`, and consumer lag for JetStream streams indicate slow consumers or poison messages.

## Implementation

Scrape `/jsz` or Prometheus metrics. Alert on rising ack_pending. Correlate with consumer pod restarts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: NATS Prometheus exporter, `nats` server varz/jsz.
• Ensure the following data sources are available: `jetstream_consumer_lag`, `ack_pending`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scrape `/jsz` or Prometheus metrics. Alert on rising ack_pending. Correlate with consumer pod restarts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=messaging sourcetype="nats:jetstream"
| where num_ack_pending > 1000 OR num_redelivered > 100
| stats max(num_ack_pending) as lag by stream_name, consumer_name
| sort -lag
```

Understanding this SPL

**NATS JetStream Consumer Ack Lag** — `NumAckPending`, `NumRedelivered`, and consumer lag for JetStream streams indicate slow consumers or poison messages.

Documented **Data sources**: `jetstream_consumer_lag`, `ack_pending`. **App/TA** (typical add-on context): NATS Prometheus exporter, `nats` server varz/jsz. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: messaging; **sourcetype**: nats:jetstream. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=messaging, sourcetype="nats:jetstream". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where num_ack_pending > 1000 OR num_redelivered > 100` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by stream_name, consumer_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ack pending), Table (stream, consumer, lag), Single value (max redelivered).

## SPL

```spl
index=messaging sourcetype="nats:jetstream"
| where num_ack_pending > 1000 OR num_redelivered > 100
| stats max(num_ack_pending) as lag by stream_name, consumer_name
| sort -lag
```

## Visualization

Line chart (ack pending), Table (stream, consumer, lag), Single value (max redelivered).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
