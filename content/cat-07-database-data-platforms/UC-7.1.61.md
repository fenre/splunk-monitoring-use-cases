<!-- AUTO-GENERATED from UC-7.1.61.json — DO NOT EDIT -->

---
id: "7.1.61"
title: "ClickHouse Disk Usage by Table and Partition"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.61 · ClickHouse Disk Usage by Table and Partition

## Description

A single partition or table consuming a disproportionate share of a host’s disk predicts `No space left` events and forces emergency TTL changes. Percent-of-host views highlight outliers even when absolute gigabytes look normal cluster-wide.

## Value

Supports proactive storage purchasing and TTL/archival decisions before ingest stops.

## Implementation

Export `SELECT database, table, partition, sum(bytes_on_disk) bytes_on_disk FROM system.parts WHERE active GROUP BY database, table, partition` daily or hourly. Normalize `partition` as string. Maintain capacity lookup for expected growth; alert when any table exceeds 25% of host disk for two consecutive runs.

## SPL

```spl
index=database sourcetype="clickhouse:parts"
| eval gb=round(tonumber(bytes_on_disk)/1073741824,3)
| stats sum(gb) as table_gb by database, table, partition, host
| eventstats sum(table_gb) as host_total by host
| eval pct_of_host=round(100*table_gb/host_total,2)
| where pct_of_host > 25 AND table_gb > 0.5
| sort -table_gb
```

## Visualization

Treemap (database.table), Table (partition, table_gb, pct_of_host).

## References

- [ClickHouse — system.parts](https://clickhouse.com/docs/en/operations/system-tables/parts)
