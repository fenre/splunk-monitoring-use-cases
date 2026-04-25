<!-- AUTO-GENERATED from UC-8.1.64.json — DO NOT EDIT -->

---
id: "8.1.64"
title: "Memcached Eviction Rate Spike Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.64 · Memcached Eviction Rate Spike Detection

## Description

Sudden eviction bursts mean working set no longer fits memory and hot keys are being discarded—latency to the origin spikes next. Delta on the `evictions` counter surfaces bursts better than absolute totals.

## Value

Prevents cache stampede scenarios during flash sales or batch jobs that pollute the working set.

## Implementation

If your collector emits per-interval deltas already, search `evictions` directly without `streamstats`. Correlate with `bytes` and `limit_maxbytes`. Scale threshold with cluster QPS.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval ev=tonumber(evictions)
| bin _time span=1m
| stats latest(ev) as evictions_cumulative by host, _time
| streamstats window=2 global=f delta(evictions_cumulative) as ev_delta by host
| where ev_delta > 1000
```

## Visualization

Line chart (ev_delta), Timeline alerts.

## References

- [Memcached wiki — eviction](https://github.com/memcached/memcached/wiki/UserManual)
