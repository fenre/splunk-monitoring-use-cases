<!-- AUTO-GENERATED from UC-8.1.73.json — DO NOT EDIT -->

---
id: "8.1.73"
title: "Memcached Expired Items vs Evicted Items Ratio"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.73 · Memcached Expired Items vs Evicted Items Ratio

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations, Data Quality &middot; **Status:** Draft

*We watch for signs that guides TTL policy and memory sizing with evidence instead of guessing from average item size alone.*

---

## Description

Healthy caches often expire items cleanly; a surge in evictions with few expirations means TTLs are too long for the working set or memory is undersized—latency becomes unpredictable.

## Value

Guides TTL policy and memory sizing with evidence instead of guessing from average item size alone.

## Implementation

Field names vary slightly by version; alias in `props.conf`. If counters absent, upgrade memcached. Use maintenance windows to ignore post-restart zero states.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval expu=tonumber(expired_unfetched)
| eval evu=tonumber(evicted_unfetched)
| bin _time span=5m
| stats latest(expu) as expired latest(evu) as evicted by host, _time
| streamstats window=2 global=f last(expired) as _prev_d_exp last(evicted) as _prev_d_ev by host
| eval d_exp = expired - _prev_d_exp, d_ev = evicted - _prev_d_ev| eval ratio=if(d_ev>0, round(d_exp/d_ev,2), null())
| where d_ev > 100 AND (isnull(ratio) OR ratio < 0.5)
```

## Visualization

Line chart (d_exp, d_ev), Single value (ratio).

## Known False Positives

Cache misses spike after cache flush, deploys with new cache keys, or during warm-up after restart. Compare with those events before treating as a fault.

## References

- [Memcached stats semantics](https://github.com/memcached/memcached/wiki/Stats)
