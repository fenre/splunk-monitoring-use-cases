<!-- AUTO-GENERATED from UC-8.1.55.json — DO NOT EDIT -->

---
id: "8.1.55"
title: "ZooKeeper Transaction Log fsync Latency Proxy"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.55 · ZooKeeper Transaction Log fsync Latency Proxy

## Description

High max latency on ZooKeeper often reflects slow txn log fsyncs or disk contention—precursors to missed heartbeats and session loss. Using `mntr` latency as a proxy avoids invasive profiling on production ensembles.

## Value

Protects low-latency metadata paths during storage maintenance or noisy-neighbor VM events.

## Implementation

Baseline latencies per hardware class. Correlate with Linux `iostat` forwarded separately. When SSD wear or RAID rebuild occurs, expect spikes—use maintenance context. Tune thresholds per AZ.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval mx=tonumber(zk_max_latency)
| eval av=tonumber(zk_avg_latency)
| where mx > 500 OR av > 100
| timechart span=1m max(mx) as max_latency_ms avg(av) as avg_latency_ms by host
```

## Visualization

Line chart (max_latency_ms), Heatmap host×time.

## References

- [ZooKeeper — Performance tuning](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_performance)
