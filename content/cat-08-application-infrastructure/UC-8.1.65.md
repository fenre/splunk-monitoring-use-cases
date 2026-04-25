<!-- AUTO-GENERATED from UC-8.1.65.json — DO NOT EDIT -->

---
id: "8.1.65"
title: "Memcached Connection Count Approaching Limit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.65 · Memcached Connection Count Approaching Limit

## Description

Memcached refuses new connections when the limit is hit, which looks like random application failures. Tracking `curr_connections` against `maxconns` gives time to recycle pools or scale out.

## Value

Avoids incident bridges caused by connection storms during deploys or mis-sized pools.

## Implementation

Add `maxconns` from instance config to each poll in your collector. Default memcached limit varies by build—never assume 1024. Alert at 85% sustained 10 minutes. Pair with app-side pool metrics.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval cur=tonumber(curr_connections)
| eval maxc=tonumber(maxconns)
| eval pct=if(maxc>0, round(100*cur/maxc,1), null())
| where pct > 85 OR cur > 10000
```

## Visualization

Gauge (pct of max), Line chart (curr_connections).

## References

- [Memcached — Connection limits](https://github.com/memcached/memcached/wiki/ConfiguringServer)
