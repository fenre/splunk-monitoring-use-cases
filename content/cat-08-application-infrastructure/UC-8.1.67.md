<!-- AUTO-GENERATED from UC-8.1.67.json — DO NOT EDIT -->

---
id: "8.1.67"
title: "Memcached Slab Class Memory Imbalance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.67 · Memcached Slab Class Memory Imbalance

## Description

When many chunks in a slab class sit free while others are exhausted, memory is stranded in the wrong slab size—evictions rise without increasing effective capacity. `stats slabs` exposes that imbalance early.

## Value

Guides tuning of slab growth, item sizes, or multi-tenant cache splits before ops teams buy RAM unnecessarily.

## Implementation

Normalize slab IDs from `stats slabs` output. Poll during low traffic to reduce cost. Combine with application object-size histogram. Restarting memcached clears slabs—use only as last resort; prefer separate pools for different object sizes.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats_slabs"
| eval pages=tonumber(total_pages)
| eval used=tonumber(used_chunks)
| eval free=tonumber(free_chunks)
| eval waste=if((used+free)>0, round(100*free/(used+free),1), null())
| where pages > 100 AND waste > 60
| stats max(waste) as max_waste by host, slab_id
| sort -max_waste
```

## Visualization

Heatmap (host × slab_id waste%), Table (top waste slabs).

## References

- [Memcached — slabs](https://github.com/memcached/memcached/wiki/Overview)
