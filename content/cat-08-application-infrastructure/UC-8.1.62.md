<!-- AUTO-GENERATED from UC-8.1.62.json — DO NOT EDIT -->

---
id: "8.1.62"
title: "ZooKeeper JVM GC Pause Correlation with Latency"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.62 · ZooKeeper JVM GC Pause Correlation with Latency

## Description

Correlating long GC pauses with elevated `zk_max_latency` differentiates JVM tuning problems from disk or network faults—critical when sessions drop without obvious external cause.

## Value

Speeds root-cause analysis and prevents repeated session storms while teams guess at network issues.

## Implementation

Align clock NTP across hosts. Tune join window (`| join max=0 ... [ | localize]`) if needed; alternatively use `transaction` or `stats` with `strptime`. Increase heap or switch GC algorithm per JVM vendor guidance when pattern repeats.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:log"
| search "Pause" OR "GC" OR "GarbageCollection"
| rex field=_raw "(?<pause_ms>\d+(\.\d+)?)\s*ms"
| where pause_ms > 200
| bin _time span=1m
| stats max(pause_ms) as gc_pause_ms by host, _time
| join type=inner host _time [
    search index=infrastructure sourcetype="zookeeper:mntr"
    | eval mx=tonumber(zk_max_latency)
    | bin _time span=1m
    | stats max(mx) as zk_max_latency_ms by host, _time
  ]
| where zk_max_latency_ms > 100
```

## Visualization

Timeline (gc_pause_ms vs zk_max_latency_ms), Table (host).

## References

- [Java GC logging (JDK 11+)](https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html#extra-options-for-java)
