<!-- AUTO-GENERATED from UC-8.1.69.json — DO NOT EDIT -->

---
id: "8.1.69"
title: "Memcached Items Stored Count Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.69 · Memcached Items Stored Count Trending

## Description

Anomalously high `curr_items` can mean TTLs were removed, cache poisoning, or unbounded key cardinality—each increases CPU for hash walks and risks eviction storms.

## Value

Catches buggy releases that stamp unbounded distinct keys before they exhaust memory metadata structures.

## Implementation

Parse `stats items` lines into `slab_id`, `number`, `age`, `evicted`, `evicted_nonzero` as your memcached version exposes. Sum `number` across slabs for total item estimate. Correlate spikes with `memcached:stats` `curr_items` on the same poll timestamp.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats_items"
| eval n=tonumber(number)
| bin _time span=1h
| stats sum(n) as items_per_slab by host, slab_id, _time
| eventstats sum(items_per_slab) as total_items by host, _time
| streamstats window=168 global=f median(total_items) as med_total by host
| where total_items > med_total*2 OR total_items > 5000000
```

## Visualization

Line chart (total_items vs median), Table (host, top slab_id).

## References

- [Memcached statistics](https://github.com/memcached/memcached/wiki/Stats)
