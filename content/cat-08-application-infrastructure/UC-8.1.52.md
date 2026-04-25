<!-- AUTO-GENERATED from UC-8.1.52.json — DO NOT EDIT -->

---
id: "8.1.52"
title: "ZooKeeper Watch Count Growth"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.52 · ZooKeeper Watch Count Growth

## Description

Each watch consumes server memory; runaway watch growth from buggy clients can pressure the JVM heap and slow all clients. Trending `zk_watch_count` exposes leaks before OutOfMemoryErrors appear.

## Value

Protects shared ZK ensembles that back many microservices from memory exhaustion due to one bad consumer.

## Implementation

Ensure `mntr` exposes `zk_watch_count` on your version. Baseline per business day; alert on sharp percentage growth. Pair with client inventory (Kafka brokers vs apps).

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval watches=tonumber(zk_watch_count)
| bin _time span=15m
| stats latest(watches) as watch_count by host, _time
| streamstats window=96 global=f first(watch_count) as baseline by host
| eval growth_pct=if(baseline>0, round(100*(watch_count-baseline)/baseline,1), null())
| where growth_pct > 50 AND watch_count > 100000
```

## Visualization

Line chart (watch_count), Table (host, growth_pct).

## References

- [ZooKeeper Jira — watch memory](https://issues.apache.org/jira/browse/ZOOKEEPER)
