<!-- AUTO-GENERATED from UC-5.14.17.json — DO NOT EDIT -->

---
id: "5.14.17"
title: "Varnish Object TTL Distribution Sampling"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.14.17 · Varnish Object TTL Distribution Sampling

## Description

TTL spread explains hit ratio and origin offload variance.

## Value

Supports data-driven cache policy reviews.

## Implementation

Sample high-volume VSL 1:N to control license cost.

## SPL

```spl
index=proxy sourcetype="varnish:vsl"
| rex field=_raw "TTL:\s+(?<ttl>\d+)"
| where isnotnull(ttl)
| bin ttl span=30
| stats count by ttl
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## References

- [Vendor documentation](https://varnish-cache.org/docs/trunk/users-guide/increasing-your-hitrate.html)
