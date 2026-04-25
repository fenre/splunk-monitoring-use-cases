<!-- AUTO-GENERATED from UC-7.2.24.json — DO NOT EDIT -->

---
id: "7.2.24"
title: "ClickHouse ReplicatedMergeTree Replication Queue Depth"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.24 · ClickHouse ReplicatedMergeTree Replication Queue Depth

## Description

A growing queue_size or large absolute_delay on ReplicatedMergeTree tables means inserts are not propagating; replicas may become inconsistent or read-only. This is primary HA monitoring for ClickHouse clusters.

## Value

Protects analytic SLAs and prevents silent replica divergence when ZooKeeper or network issues slow replication.

## Implementation

Poll system.replicas every minute for production tables. Alert on queue_size and absolute_delay thresholds tuned to insert volume. Correlate with ZooKeeper latency and background pool metrics.

## SPL

```spl
index=database sourcetype="clickhouse:replicas"
| eval lag_ops=log_max_index-log_pointer
| where queue_size > 1000 OR absolute_delay > 300 OR is_readonly==1
| stats max(queue_size) as max_queue max(absolute_delay) as max_delay_sec by database, table, host
| sort -max_queue
```

## Visualization

Line chart (queue_size by table), Table (top delays), Single value (read-only replicas).

## References

- [ClickHouse system.replicas](https://clickhouse.com/docs/en/operations/system-tables/replicas)
