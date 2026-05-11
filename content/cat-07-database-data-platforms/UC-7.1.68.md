<!-- AUTO-GENERATED from UC-7.1.68.json — DO NOT EDIT -->

---
id: "7.1.68"
title: "Cassandra Read and Write Latency P99 by Keyspace"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.68 · Cassandra Read and Write Latency P99 by Keyspace

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Status:** Draft

*We watch Cassandra Read and Write Latency P99 by Keyspace so we can keep this part of the data platform within the capacity and quality targets our teams expect.*

---

## Description

Table-level 99th percentile latencies isolate hot partitions and compaction debt before mean cluster metrics move. Keyspace-level rollups help tenant owners understand SLA risk on shared rings.

## Value

Prevents customer-visible timeouts by steering tuning (compaction, caching, consistency level) to the right tables.

## Implementation

Normalize nodetool output: map `Keyspace`, `Table`, and latency percentiles to consistent field names (`keyspace_name`, `table_name`, `Percentile_99th_read_latency_ms`). Poll every 5 minutes. If your C* version prints microseconds, convert in `props.conf` `EVAL`. Join with application release calendar for correlation.

## SPL

```spl
index=database sourcetype="cassandra:nodetool_cfstats"
| eval r99=tonumber(Percentile_99th_read_latency_ms)
| eval w99=tonumber(Percentile_99th_write_latency_ms)
| where r99 > 50 OR w99 > 50
| stats max(r99) as read_p99_ms max(w99) as write_p99_ms by keyspace_name, table_name, host
| sort -read_p99_ms
```

## Visualization

Heatmap (keyspace × host for read_p99_ms), Line chart trends.

## Known False Positives

Repairs, bootstraps, and heavy write bursts increase compaction and hinted-handoff backlog as part of normal Cassandra self-healing — alert on stuck or growing queues outside known batch jobs.

## References

- [Apache Cassandra — nodetool tablestats](https://cassandra.apache.org/doc/latest/cassandra/)
