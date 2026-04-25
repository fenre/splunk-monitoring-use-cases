<!-- AUTO-GENERATED from UC-7.1.41.json — DO NOT EDIT -->

---
id: "7.1.41"
title: "PostgreSQL Checkpoint and Background Writer Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.41 · PostgreSQL Checkpoint and Background Writer Pressure

## Description

Requested checkpoints (checkpoints_req) and bgwriter truncations (maxwritten_clean) spike when checkpoints cannot keep pace with dirty buffers, causing I/O stalls and query latency. Monitoring pg_stat_bgwriter is a standard PostgreSQL tuning signal.

## Value

Surfaces checkpoint overload before sustained write stalls, long recovery times, and tail latency regressions on write-heavy PostgreSQL clusters.

## Implementation

Schedule a DB Connect rising column or time-based query against pg_stat_bgwriter every 60 seconds. Normalize host and cluster. Baseline checkpoints_req per workload; alert on sustained elevation versus checkpoints_timed. Pair with pg_stat_checkpointer on PostgreSQL 17+ if available.

## SPL

```spl
index=database sourcetype="postgresql:bgwriter"
| eval req_ratio=if(checkpoints_timed>0, round(checkpoints_req/checkpoints_timed,3), null())
| where checkpoints_req > 10 OR maxwritten_clean > 100 OR req_ratio > 0.5
| timechart span=15m sum(checkpoints_req) as checkpoints_requested, sum(maxwritten_clean) as bgwriter_truncations by host
```

## Visualization

Line chart (checkpoints_req vs checkpoints_timed), Single value (maxwritten_clean), Table (host, buffers_checkpoint, write time).

## References

- [PostgreSQL Statistics Collector — pg_stat_bgwriter](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-BGWRITER-VIEW)
- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
