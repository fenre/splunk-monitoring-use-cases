<!-- AUTO-GENERATED from UC-8.1.63.json — DO NOT EDIT -->

---
id: "8.1.63"
title: "Memcached Hit Ratio Trending"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.63 · Memcached Hit Ratio Trending

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Operational &middot; **Status:** Draft

*We watch for signs that keeps read-mostly workloads fast and protects origin databases during traffic surges.*

---

## Description

Falling cache hit ratio means more requests fall through to the backing database, raising latency and cost. Tracking ratio over fixed windows isolates application or TTL regressions before DB CPU spikes.

## Value

Keeps read-mostly workloads fast and protects origin databases during traffic surges.

## Implementation

Poll `stats` every 10–30s; extract `get_hits`, `get_misses`, `curr_connections`. Use incremental counters and `delta` in Splunk if you ingest cumulative totals. Baseline per application; some caches legitimately run 50% hit rates—tune thresholds accordingly.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval hits=tonumber(get_hits)
| eval misses=tonumber(get_misses)
| bin _time span=5m
| stats sum(hits) as hits sum(misses) as misses by host, _time
| eval hit_ratio=round(hits/(hits+misses+0.001)*100,2)
| where hit_ratio < 70
```

## Visualization

Line chart (hit_ratio), Dual axis (hits, misses).

## Known False Positives

Cache misses spike after cache flush, deploys with new cache keys, or during warm-up after restart. Compare with those events before treating as a fault.

## References

- [Memcached protocol — stats](https://github.com/memcached/memcached/blob/master/doc/protocol.txt)
