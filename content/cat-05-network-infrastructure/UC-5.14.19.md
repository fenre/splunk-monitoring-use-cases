<!-- AUTO-GENERATED from UC-5.14.19.json — DO NOT EDIT -->

---
id: "5.14.19"
title: "Varnish SMA Allocator Free Ratio Watch"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.19 · Varnish SMA Allocator Free Ratio Watch

## Description

Fragmentation silently shrinks effective cache space.

## Value

Triggers proactive rebuilds or storage backend changes.

## Implementation

Map counter names per version; plan storage migration if chronic fragmentation.

## SPL

```spl
index=proxy sourcetype="varnish:stats"
| eval alloc=tonumber(sma_bytes_allocated), free=tonumber(sma_bytes_free)
| eval free_pct=if((alloc+free)>0, round(100*free/(alloc+free),1), null())
| where free_pct > 40
| table host, alloc, free, free_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/storage-backends.html)
