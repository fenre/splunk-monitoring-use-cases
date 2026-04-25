<!-- AUTO-GENERATED from UC-8.3.1.json — DO NOT EDIT -->

---
id: "8.3.1"
title: "Consumer Lag Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.3.1 · Consumer Lag Monitoring

## Description

Growing consumer lag means messages aren't being processed fast enough, leading to data staleness and eventual message loss if retention is exceeded.

## Value

Growing consumer lag means messages aren't being processed fast enough, leading to data staleness and eventual message loss if retention is exceeded.

## Implementation

Deploy Kafka consumer lag monitoring via Burrow or JMX. Poll lag per consumer group/topic/partition every minute. Alert when lag exceeds threshold (e.g., >10K messages or >5 minutes equivalent). Track lag trend for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk Connect for Kafka` (Splunkbase 3862), Burrow integration, JMX.
• Ensure the following data sources are available: Kafka consumer group offsets (JMX, Burrow, `kafka-consumer-groups.sh`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Kafka consumer lag monitoring via Burrow or JMX. Poll lag per consumer group/topic/partition every minute. Alert when lag exceeds threshold (e.g., >10K messages or >5 minutes equivalent). Track lag trend for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:consumer_lag"
| timechart span=5m max(lag) as consumer_lag by consumer_group, topic
| where consumer_lag > 10000
```

Understanding this SPL

**Consumer Lag Monitoring** — Growing consumer lag means messages aren't being processed fast enough, leading to data staleness and eventual message loss if retention is exceeded.

Documented **Data sources**: Kafka consumer group offsets (JMX, Burrow, `kafka-consumer-groups.sh`). **App/TA** (typical add-on context): `Splunk Connect for Kafka` (Splunkbase 3862), Burrow integration, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:consumer_lag. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:consumer_lag". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by consumer_group, topic** — ideal for trending and alerting on this use case.
• Filters the current rows with `where consumer_lag > 10000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (lag per consumer group), Heatmap (topic × partition lag), Single value (max lag), Table (lagging consumers).

## SPL

```spl
index=kafka sourcetype="kafka:consumer_lag"
| timechart span=5m max(lag) as consumer_lag by consumer_group, topic
| where consumer_lag > 10000
```

## Visualization

Line chart (lag per consumer group), Heatmap (topic × partition lag), Single value (max lag), Table (lagging consumers).

## References

- [Splunkbase app 3862](https://splunkbase.splunk.com/app/3862)
