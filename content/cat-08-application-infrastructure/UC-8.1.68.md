<!-- AUTO-GENERATED from UC-8.1.68.json — DO NOT EDIT -->

---
id: "8.1.68"
title: "Memcached CAS Bad Value Contention Rate"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.68 · Memcached CAS Bad Value Contention Rate

## Description

`cas_badval` increments when compare-and-swap races fail—usually hot keys updated by many writers. High contention wastes CPU and signals logical races that can surface as stale reads in applications.

## Value

Helps application teams switch to app-level locking, sharded keys, or CRDT patterns before incidents during high concurrency.

## Implementation

Ensure extended stats are enabled in collector. If counter missing, upgrade memcached or enable full stats. Baseline per service; some CAS-heavy apps always show noise—use ratio to `cas_hits` if available.

## SPL

```spl
index=infrastructure sourcetype="memcached:stats"
| eval bad=tonumber(cas_badval)
| bin _time span=5m
| stats latest(bad) as cas_bad by host, _time
| streamstats window=2 global=f delta(cas_bad) as cas_bad_delta by host
| where cas_bad_delta > 100
```

## Visualization

Line chart (cas_bad_delta), Table (host).

## References

- [Memcached CAS operations](https://github.com/memcached/memcached/wiki/ProgrammingTricks)
