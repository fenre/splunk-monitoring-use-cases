<!-- AUTO-GENERATED from UC-7.1.50.json — DO NOT EDIT -->

---
id: "7.1.50"
title: "MongoDB WiredTiger Dirty Cache Percentage Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.50 · MongoDB WiredTiger Dirty Cache Percentage Trending

## Description

A rising share of the WiredTiger cache held as dirty pages means checkpoints and eviction are falling behind, which precedes IO storms and tail latency on transactional workloads. Tracking dirty percentage relative to its own baseline catches gradual regressions before absolute thresholds trip.

## Value

Lets capacity owners add cache, smooth write bursts, or reschedule index builds before application teams see p95 latency cliffs during peak traffic.

## Implementation

Install the Splunk Add-on for MongoDB and enable the `serverStatus` scripted/modular input in `inputs.conf` (interval 60–300s). Map `wiredTiger.cache.bytes dirty in the cache` and `bytes currently in the cache` to `bytes_dirty` and `bytes_currently_in_the_cache`. Normalize host/cluster tags in `props.conf` if needed. Alert when dirty_pct exceeds 25% and is 10 points above the prior 90-minute baseline for the same host.

## SPL

```spl
index=database sourcetype="mongodb:server_status"
| eval dirty_pct=if(bytes_currently_in_the_cache>0, round(100*bytes_dirty/bytes_currently_in_the_cache,2), null())
| bin _time span=15m
| stats latest(dirty_pct) as dirty_pct by host, _time
| streamstats window=6 global=f first(dirty_pct) as baseline by host
| where dirty_pct > 25 AND dirty_pct > baseline+10
```

## Visualization

Line chart (dirty_pct by host), Single value (worst host), Table (host, dirty_pct, baseline delta).

## References

- [MongoDB WiredTiger cache tuning](https://www.mongodb.com/docs/manual/administration/analyzing-mongodb-performance/#wiredtiger-cache)
- [Splunk Add-on for MongoDB](https://splunkbase.splunk.com/app/3212)
