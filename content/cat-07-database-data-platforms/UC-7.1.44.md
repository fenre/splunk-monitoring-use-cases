<!-- AUTO-GENERATED from UC-7.1.44.json — DO NOT EDIT -->

---
id: "7.1.44"
title: "ClickHouse Merge Throughput and Backlog"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.44 · ClickHouse Merge Throughput and Backlog

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We track replication and apply lag so we can meet recovery and read-your-writes expectations when a region or network path is under stress.*

---

## Description

Large merges or merges that run for many minutes increase read amplification and delay parts optimization. Operators monitor system.merges alongside parts counts to catch storage engine pressure early.

## Value

Avoids query timeouts and replication delay caused by merge storms or stuck wide parts on ClickHouse merge-tree tables.

## Implementation

Poll system.merges every minute; emit one event per active merge with database, table, progress, num_parts, elapsed, result_part_name. Track merge width (num_parts) and wall time. Correlate with insert rate and TTL mutations.

## SPL

```spl
index=database sourcetype="clickhouse:merges"
| eval elapsed_sec=elapsed
| where num_parts > 50 OR elapsed_sec > 600
| stats count as active_merges, avg(progress) as avg_progress_pct, max(elapsed_sec) as max_elapsed by database, table, host
| sort -active_merges
```

## Visualization

Table (wide merges), Line chart (active merge count), Histogram (elapsed).

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [ClickHouse system.merges](https://clickhouse.com/docs/en/operations/system-tables/merges)
