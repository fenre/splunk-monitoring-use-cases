<!-- AUTO-GENERATED from UC-8.1.70.json — DO NOT EDIT -->

---
id: "8.1.70"
title: "Memcached GET and SET Operations Throughput"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.70 · Memcached GET and SET Operations Throughput

## Description

Throughput anomalies—sudden 10× jumps or drops—often align with cache bypass bugs, DDoS, or failed upstream failovers. Normalized per-second rates make clusters comparable.

## Value

Speeds incident correlation when databases spike alongside unusual cache traffic patterns.

## Implementation

If collector emits rates directly, drop `delta` logic. Tag `app` or `pool` in `_meta` from chef/ansible. Alert thresholds must match hardware (network and single-thread limits).

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval g=tonumber(cmd_get)
| eval s=tonumber(cmd_set)
| bin _time span=1m
| stats latest(g) as gets latest(s) as sets by host, _time
| streamstats window=2 global=f delta(gets) as get_rps delta(sets) as set_rps by host
| eval get_rps=round(get_rps/60,0)
| eval set_rps=round(set_rps/60,0)
| where get_rps > 50000 OR set_rps > 20000
```

## Visualization

Line chart (get_rps, set_rps), Single value peak QPS.

## References

- [Memcached protocol](https://github.com/memcached/memcached/blob/master/doc/protocol.txt)
