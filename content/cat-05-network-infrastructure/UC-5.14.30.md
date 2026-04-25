<!-- AUTO-GENERATED from UC-5.14.30.json — DO NOT EDIT -->

---
id: "5.14.30"
title: "Squid Memory Hit vs Disk Hit Distribution"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.14.30 · Squid Memory Hit vs Disk Hit Distribution

## Description

Mis-tuned memory leaves performance on the table.

## Value

Improves latency for hot assets.

## Implementation

Tune `cache_mem` versus disk to shift hot objects to RAM.

## SPL

```spl
index=proxy sourcetype="squid:access"
| eval layer=case(match(code, "TCP_MEM_HIT"),"mem", match(code, "TCP_HIT|TCP_REFRESH_HIT"),"disk", true(), "other")
| bin _time span=15m
| stats count by layer, _time
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/cache_mem/)
