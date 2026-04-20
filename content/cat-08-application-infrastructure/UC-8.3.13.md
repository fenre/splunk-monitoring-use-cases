---
id: "8.3.13"
title: "Kafka Consumer Lag Monitoring (Consumer Group)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.13 · Kafka Consumer Lag Monitoring (Consumer Group)

## Description

Lag in messages and approximate time lag per partition for each `group.id`. Tightens UC-8.3.1 with `kafka-consumer-groups` export fields.

## Value

Lag in messages and approximate time lag per partition for each `group.id`. Tightens UC-8.3.1 with `kafka-consumer-groups` export fields.

## Implementation

Poll `kafka-consumer-groups.sh --describe` every minute. Alert on lag > SLA messages or estimated seconds. Exclude bursty batch groups via lookup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Burrow, Kafka Connect, `kafka:consumer_lag` scripted input.
• Ensure the following data sources are available: `LAG`, `CONSUMER-ID`, `TOPIC`, `PARTITION`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `kafka-consumer-groups.sh --describe` every minute. Alert on lag > SLA messages or estimated seconds. Exclude bursty batch groups via lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:consumer_lag"
| eval lag_sec=coalesce(lag_seconds, estimated_lag_sec)
| where lag > 100000 OR lag_sec > 300
| timechart span=5m max(lag) as max_lag by consumer_group, topic
```

Understanding this SPL

**Kafka Consumer Lag Monitoring (Consumer Group)** — Lag in messages and approximate time lag per partition for each `group.id`. Tightens UC-8.3.1 with `kafka-consumer-groups` export fields.

Documented **Data sources**: `LAG`, `CONSUMER-ID`, `TOPIC`, `PARTITION`. **App/TA** (typical add-on context): Burrow, Kafka Connect, `kafka:consumer_lag` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:consumer_lag. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:consumer_lag". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where lag > 100000 OR lag_sec > 300` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by consumer_group, topic** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (lag by group/topic), Heatmap (partition lag), Single value (worst consumer group).

## SPL

```spl
index=kafka sourcetype="kafka:consumer_lag"
| eval lag_sec=coalesce(lag_seconds, estimated_lag_sec)
| where lag > 100000 OR lag_sec > 300
| timechart span=5m max(lag) as max_lag by consumer_group, topic
```

## Visualization

Line chart (lag by group/topic), Heatmap (partition lag), Single value (worst consumer group).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
