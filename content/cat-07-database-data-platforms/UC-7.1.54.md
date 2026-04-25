<!-- AUTO-GENERATED from UC-7.1.54.json — DO NOT EDIT -->

---
id: "7.1.54"
title: "ClickHouse Query Duration P95 and P99 from Query Log"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.54 · ClickHouse Query Duration P95 and P99 from Query Log

## Description

Percentile latency drift in `query_log` is an early signal of CPU, disk, or merge pressure before mean metrics move. Segmenting by `query_kind` keeps ETL batch noise separate from interactive SELECT SLAs.

## Value

Protects analyst and application SLAs by catching regressions tied to schema or data volume changes early.

## Implementation

Enable `query_log` in `config.xml` (`query_log` section) with appropriate flush interval. Export finished queries only (`type` = QueryFinish / numeric 2 depending on version). Map `query_duration_ms`, `query_kind`, `user`, `read_rows` at index time. Baseline per workload class; tune thresholds per environment.

## SPL

```spl
index=database sourcetype="clickhouse:query_log"
| where type==2 OR type=="QueryFinish" OR match(_raw,"QueryFinish")
| bin _time span=1h
| stats perc95(query_duration_ms) as p95_ms perc99(query_duration_ms) as p99_ms count by query_kind, host, _time
| where p95_ms > 5000 OR p99_ms > 30000
```

## Visualization

Line chart (p95_ms, p99_ms by query_kind), Heatmap (hour × query_kind).

## References

- [ClickHouse — query_log](https://clickhouse.com/docs/en/operations/system-tables/query_log)
