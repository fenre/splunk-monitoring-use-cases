<!-- AUTO-GENERATED from UC-7.1.63.json — DO NOT EDIT -->

---
id: "7.1.63"
title: "ClickHouse INSERT Throughput and Batch Row Efficiency"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.63 · ClickHouse INSERT Throughput and Batch Row Efficiency

## Description

Tiny insert batches inflate part count and merge pressure even when nominal QPS looks fine. Monitoring median throughput and batch row percentiles exposes anti-patterns from application drivers before merge backlogs form.

## Value

Guards ingestion pipelines against accidental per-row inserts that degrade cluster-wide performance.

## Implementation

Ensure `written_rows` and `query_kind` are extracted for HTTP and native insert paths. Baseline med_rps per workload; tune thresholds per table. Pair with `clickhouse:parts` active_parts panel. Work with app teams to raise batch sizes or use async insert settings.

## SPL

```spl
index=database sourcetype="clickhouse:query_log"
| where query_kind="Insert"
| eval rows_written=tonumber(written_rows)
| eval dur_ms=tonumber(query_duration_ms)
| eval rows_per_sec=if(dur_ms>0, round(1000*rows_written/dur_ms,0), null())
| bin _time span=15m
| stats median(rows_per_sec) as med_rps p10(rows_written) as p10_batch_rows by host, _time
| where p10_batch_rows < 1000 AND med_rps < 50000
```

## Visualization

Line chart (med_rps, p10_batch_rows), Scatter (written_rows vs duration).

## References

- [ClickHouse — Insert best practices](https://clickhouse.com/docs/en/guides/best-practices/sparse-primary-indexes)
