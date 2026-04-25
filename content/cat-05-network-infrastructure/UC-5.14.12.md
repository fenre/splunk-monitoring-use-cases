<!-- AUTO-GENERATED from UC-5.14.12.json — DO NOT EDIT -->

---
id: "5.14.12"
title: "Varnish LRU Nuked Objects Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.12 · Varnish LRU Nuked Objects Rate

## Description

Rising nukes predict hit ratio collapse and origin storms.

## Value

Informs malloc/file storage sizing decisions.

## Implementation

Correlate spikes with origin load; revisit storage size and TTL policies.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval nuked=tonumber(n_lru_nuked)
| sort 0 host _time
| streamstats window=2 global=f last(nuked) as p_n by host
| eval d=nuked-p_n
| timechart span=5m sum(d) as lru_nukes by host
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/storage-backends.html)
