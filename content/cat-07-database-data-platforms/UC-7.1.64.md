<!-- AUTO-GENERATED from UC-7.1.64.json — DO NOT EDIT -->

---
id: "7.1.64"
title: "ClickHouse Background Pool Saturation (Merges vs Mutations)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.64 · ClickHouse Background Pool Saturation (Merges vs Mutations)

## Description

When background merge and mutation pools stay saturated, new parts accumulate and interactive queries queue behind maintenance work. Metric spikes differentiate normal batch windows from pathological contention.

## Value

Prevents cascading latency where operational DDL and ingestion compete for the same thread pools.

## Implementation

Map exact metric names from your ClickHouse version (`system.metrics` / asynchronous_metrics). Some deployments expose `BackgroundSchedulePoolTask`. Create a baseline per business day. Correlate with `clickhouse:merges` active merge count and running mutations search.

## SPL

```spl
index=database (sourcetype="clickhouse:asynchronous_metrics" OR sourcetype="clickhouse:system_events")
| search metric IN ("BackgroundMergePoolTask","BackgroundMergesAndMutationsPoolTask","Mutation") OR match(metric,"Merge")
| eval v=tonumber(value)
| bin _time span=5m
| stats avg(v) as pool_tasks by metric, host, _time
| eventstats avg(pool_tasks) as baseline by metric, host
| where pool_tasks > baseline*2 AND pool_tasks > 10
```

## Visualization

Line chart (pool_tasks by metric), Overlay with active merges count.

## References

- [ClickHouse — system.metrics](https://clickhouse.com/docs/en/operations/system-tables/metrics)
