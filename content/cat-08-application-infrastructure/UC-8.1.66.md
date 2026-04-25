<!-- AUTO-GENERATED from UC-8.1.66.json — DO NOT EDIT -->

---
id: "8.1.66"
title: "Memcached Memory Usage vs maxbytes Threshold"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.66 · Memcached Memory Usage vs maxbytes Threshold

## Description

When `bytes` approaches `limit_maxbytes`, evictions accelerate and new large items may fail. Watching used percentage avoids surprise latency cliffs during traffic growth.

## Value

Supports right-sizing memory per cluster before peak events exhaust slab space.

## Implementation

Confirm 64-bit counters parse correctly. For multiple instances per host, include `instance` or `port` in the host key. Alert at 90% with warning; 95% page on-call.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval used=tonumber(bytes)
| eval lim=tonumber(limit_maxbytes)
| eval used_pct=if(lim>0, round(100*used/lim,1), null())
| where used_pct > 90 OR used > lim*0.95
```

## Visualization

Area chart (used vs lim), Gauge (used_pct).

## References

- [Memcached — Memory allocation](https://github.com/memcached/memcached/wiki/UserManual)
