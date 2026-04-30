<!-- AUTO-GENERATED from UC-7.2.24.json — DO NOT EDIT -->

---
id: "7.2.24"
title: "ClickHouse ReplicatedMergeTree Replication Queue Depth"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.24 · ClickHouse ReplicatedMergeTree Replication Queue Depth

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

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

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [ClickHouse system.replicas](https://clickhouse.com/docs/en/operations/system-tables/replicas)
