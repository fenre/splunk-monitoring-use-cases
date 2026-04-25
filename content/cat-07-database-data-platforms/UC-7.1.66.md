<!-- AUTO-GENERATED from UC-7.1.66.json — DO NOT EDIT -->

---
id: "7.1.66"
title: "ClickHouse Kafka Engine Table Consumer Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.66 · ClickHouse Kafka Engine Table Consumer Lag

## Description

Kafka engine tables stall when consumers cannot parse messages, commit offsets, or keep up with producers; downstream materialized views then serve stale analytics. Error bursts in `StorageKafka` logs pinpoint the table and host faster than broker-only lag dashboards.

## Value

Protects near-real-time pipelines feeding fraud detection and operations KPIs from silent backlog growth.

## Implementation

Prefer exporting `SELECT * FROM system.kafka_consumers` when available (fields like `assignments`, `exceptions` vary by version). Complement with server log monitoring as above. Correlate with Kafka broker metrics and ClickHouse `max_insert_block_size`. Tune alert for error rate vs baseline.

## SPL

```spl
index=database sourcetype="clickhouse:server_log"
| search "StorageKafka" AND ("Exception" OR "ERROR" OR "Failed to commit" OR "RDKAFKA")
| rex field=_raw "table\s+`?(?<kafka_table>[\w\.]+)`?"
| bin _time span=5m
| stats count as errors by kafka_table, host, _time
| where errors >= 10
```

## Visualization

Timeline (errors), Table (kafka_table, host), Single value (open consumer exceptions).

## References

- [ClickHouse — Kafka engine](https://clickhouse.com/docs/en/engines/table-engines/integrations/kafka)
