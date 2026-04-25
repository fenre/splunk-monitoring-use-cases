<!-- AUTO-GENERATED from UC-5.14.9.json — DO NOT EDIT -->

---
id: "5.14.9"
title: "Varnish Cache Hit Ratio Trending (HIT vs MISS vs PASS)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.9 · Varnish Cache Hit Ratio Trending (HIT vs MISS vs PASS)

## Description

Hit ratio ties origin cost and latency directly to cache effectiveness.

## Value

Guides TTL, grace, and storage tuning with measurable outcomes.

## Implementation

Ship VSL via `varnishncsa` custom format or HEC JSON lines. For counter view add `varnish:stats` companion panel.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| eval hit=if(match(_raw, "(?i)\bHIT\b|VCL_hit"),1,0)
| eval miss=if(match(_raw, "(?i)VCL_miss|\bMISS\b"),1,0)
| eval pass=if(match(_raw, "(?i)VCL_pass|\bPASS\b"),1,0)
| bin _time span=5m
| stats sum(hit) as hits sum(miss) as misses sum(pass) as passes
| eval hit_ratio=round(100*hits/(hits+misses+passes+0.001),2)
| timechart span=5m avg(hit_ratio) as hit_pct
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/intro.html)
