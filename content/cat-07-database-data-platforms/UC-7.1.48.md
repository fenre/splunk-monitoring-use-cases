<!-- AUTO-GENERATED from UC-7.1.48.json — DO NOT EDIT -->

---
id: "7.1.48"
title: "MySQL InnoDB Redo Log Wait Pressure"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.48 · MySQL InnoDB Redo Log Wait Pressure

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We track replication and apply lag so we can meet recovery and read-your-writes expectations when a region or network path is under stress.*

---

## Description

Innodb_log_waits increments when user threads wait on the redo log buffer—an indicator of bursty writes, undersized redo capacity, or storage latency on MySQL 8.

## Value

Catches redo-induced stalls before they become widespread transaction latency and replication lag.

## Implementation

Poll global status at fixed intervals and compute deltas for counter fields. Validate Innodb_log_waits exists on your minor version. Correlate with disk latency metrics and innodb_redo_log_capacity changes.

## SPL

```spl
index=database sourcetype="mysql:status"
| timechart span=15m latest(Innodb_log_waits) as innodb_log_waits by host
| streamstats window=2 global=f delta(innodb_log_waits) as log_waits_delta by host
| where log_waits_delta > 10
```

## Visualization

Line chart (redo waits per interval), Table (hosts, delta), Single value (total waits).

## Known False Positives

Cold caches right after restarts, failover, or one-off full scans can lower hit ratios until the working set is warm again — watch trends, not a single low sample.

## References

- [MySQL InnoDB redo logging](https://dev.mysql.com/doc/refman/8.0/en/innodb-redo-log.html)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
