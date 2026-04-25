<!-- AUTO-GENERATED from UC-8.3.17.json — DO NOT EDIT -->

---
id: "8.3.17"
title: "Kafka Topic Partition Skew"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.3.17 · Kafka Topic Partition Skew

## Description

Byte size and message count skew across partitions causes hot brokers and uneven consumer lag. Uses `kafka-log-dirs` or broker metrics.

## Value

Byte size and message count skew across partitions causes hot brokers and uneven consumer lag. Uses `kafka-log-dirs` or broker metrics.

## Implementation

Nightly job from log size per partition. Alert when skew >25%. Recommend partition key review or reassign.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, broker metrics export.
• Ensure the following data sources are available: `Size` per partition, `LogEndOffset` per partition.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Nightly job from log size per partition. Alert when skew >25%. Recommend partition key review or reassign.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=kafka sourcetype="kafka:partition_skew"
| eventstats avg(partition_size_bytes) as avg_sz by topic
| eval skew_pct=round(abs(partition_size_bytes-avg_sz)/avg_sz*100,1)
| where skew_pct > 25
| table topic partition partition_size_bytes skew_pct
```

Understanding this SPL

**Kafka Topic Partition Skew** — Byte size and message count skew across partitions causes hot brokers and uneven consumer lag. Uses `kafka-log-dirs` or broker metrics.

Documented **Data sources**: `Size` per partition, `LogEndOffset` per partition. **App/TA** (typical add-on context): JMX, broker metrics export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: kafka; **sourcetype**: kafka:partition_skew. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=kafka, sourcetype="kafka:partition_skew". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eventstats` rolls up events into metrics; results are split **by topic** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **skew_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where skew_pct > 25` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Kafka Topic Partition Skew**): table topic partition partition_size_bytes skew_pct

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with the broker or gateway’s own UI or CLI (`kafka-consumer-groups`, RabbitMQ management, ActiveMQ console, or Traefik/Envoy access log on the node) for the same period.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (skew % by partition), Table (top skewed topics), Heatmap (broker × partition size).

## SPL

```spl
index=kafka sourcetype="kafka:partition_skew"
| eventstats avg(partition_size_bytes) as avg_sz by topic
| eval skew_pct=round(abs(partition_size_bytes-avg_sz)/avg_sz*100,1)
| where skew_pct > 25
| table topic partition partition_size_bytes skew_pct
```

## Visualization

Bar chart (skew % by partition), Table (top skewed topics), Heatmap (broker × partition size).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
