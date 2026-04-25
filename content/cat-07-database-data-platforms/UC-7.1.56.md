<!-- AUTO-GENERATED from UC-7.1.56.json — DO NOT EDIT -->

---
id: "7.1.56"
title: "ClickHouse ReplicatedMergeTree Replica Read-Only Mode and Absolute Delay"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.56 · ClickHouse ReplicatedMergeTree Replica Read-Only Mode and Absolute Delay

## Description

A deep `queue_size` or rising `absolute_delay` means replicas are not applying log entries fast enough, which risks read inconsistency and recovery time after failures. Read-only mode transitions often precede user-visible errors.

## Value

Supports HA commitments on ReplicatedMergeTree by catching ZooKeeper/network/part issues before replicas diverge or queries fail.

## Implementation

Poll `SELECT database, table, queue_size, absolute_delay, is_readonly FROM system.replicas` on each node every 60s. Normalize booleans. Alert queue_size >1000 (tune per table size) or sustained growth over 30 minutes. Correlate with `clickhouse:server_log` ZooKeeper errors.

## SPL

```spl
index=database sourcetype="clickhouse:replicas"
| eval q=tonumber(queue_size)
| where q > 500 OR is_readonly==1 OR is_readonly=="true"
| stats max(q) as max_queue latest(absolute_delay) as abs_delay_sec by database, table, host
| sort -max_queue
```

## Visualization

Line chart (queue_size by table), Single value (max queue), Table (database, table, host, is_readonly).

## References

- [ClickHouse — system.replicas](https://clickhouse.com/docs/en/operations/system-tables/replicas)
