<!-- AUTO-GENERATED from UC-7.4.21.json — DO NOT EDIT -->

---
id: "7.4.21"
title: "Redis used_memory Headroom vs maxmemory"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.21 · Redis used_memory Headroom vs maxmemory

## Description

When used_memory approaches maxmemory, eviction or OOM behavior follows. Capacity monitoring uses the ratio to maxmemory as the primary early warning.

## Value

Prevents sudden eviction storms and write failures on memory-bound Redis clusters.

## Implementation

Poll INFO memory section every minute. Treat maxmemory=0 as unlimited and skip ratio alerts (use absolute used_memory trends instead). Separate primary and replica roles. Pair with UC eviction rate monitoring.

## SPL

```spl
index=middleware sourcetype="redis:info"
| where maxmemory > 0
| eval mem_pct=round(used_memory/maxmemory*100,2)
| where mem_pct > 90
| timechart span=5m max(mem_pct) as used_pct by host, role
```

## Visualization

Gauge (used % of max), Line chart (used_memory), Table (hosts over threshold).

## References

- [Redis memory optimization](https://redis.io/docs/latest/develop/use/keyspace/)
