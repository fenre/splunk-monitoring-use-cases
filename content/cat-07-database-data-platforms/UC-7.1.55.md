<!-- AUTO-GENERATED from UC-7.1.55.json — DO NOT EDIT -->

---
id: "7.1.55"
title: "ClickHouse Distributed Query Inter-Shard Latency"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.55 · ClickHouse Distributed Query Inter-Shard Latency

## Description

Skewed shard execution shows up as some nodes finishing far slower than the cluster max for the same `initial_query_id`, which inflates end-to-end latency for distributed tables. Finding those slow shards guides network, disk, and hot-part investigations.

## Value

Prevents long-running analytics queries from starving business dashboards when one replica or shard is unhealthy.

## Implementation

Ensure `query_log` retains `initial_query_id`, `query_id`, `host`, `is_initial_query`, and `query_duration_ms`. For sharded clusters, include the emitting node's hostname in each event. Schedule search every 15 minutes; validate `initial_query_id` population on your ClickHouse version and adjust `is_initial_query` filter accordingly.

## SPL

```spl
index=database sourcetype="clickhouse:query_log"
| where (is_initial_query==1 OR is_initial_query=="true") AND query_kind="Select"
| eval root_id=coalesce(initial_query_id, query_id)
| stats max(query_duration_ms) as max_leaf_ms by root_id, host
| eventstats max(max_leaf_ms) as cluster_max by root_id
| eval skew_ratio=if(cluster_max>0, round(max_leaf_ms/cluster_max,3), null())
| where skew_ratio < 0.2 AND max_leaf_ms > 10000
| stats values(host) as slow_shards dc(root_id) as affected_queries
```

## Visualization

Table (root_id, slow_shards, max_leaf_ms), Sankey or chord optional if enriched with cluster topology.

## References

- [ClickHouse — Distributed engine](https://clickhouse.com/docs/en/engines/table-engines/special/distributed)
