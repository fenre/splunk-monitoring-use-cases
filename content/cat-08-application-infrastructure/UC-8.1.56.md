<!-- AUTO-GENERATED from UC-8.1.56.json — DO NOT EDIT -->

---
id: "8.1.56"
title: "ZooKeeper Request Latency P95 and P99 from mntr"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.56 · ZooKeeper Request Latency P95 and P99 from mntr

## Description

Average and max latency percentiles summarize client-visible slowness better than single snapshots. Rising p95 with stable load often precedes capacity limits on CPU or txn log devices.

## Value

Supports SLO dashboards for platform teams owning shared ZooKeeper clusters.

## Implementation

Collect dense enough samples for meaningful percentiles (≤10s). Do not enable `mntr` from untrusted networks. Store per-ensemble index. Compare across rolling upgrades.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval avg_lat=tonumber(zk_avg_latency)
| eval max_lat=tonumber(zk_max_latency)
| bin _time span=5m
| stats perc95(avg_lat) as p95_avg perc99(max_lat) as p99_max by host, _time
| where p95_avg > 50 OR p99_max > 200
```

## Visualization

Line chart (p95_avg, p99_max), Table (host outliers).

## References

- [ZooKeeper — Monitoring](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_monitoring)
