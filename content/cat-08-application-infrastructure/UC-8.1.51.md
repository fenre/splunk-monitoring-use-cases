<!-- AUTO-GENERATED from UC-8.1.51.json — DO NOT EDIT -->

---
id: "8.1.51"
title: "ZooKeeper Outstanding Requests Queue Depth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.51 · ZooKeeper Outstanding Requests Queue Depth

## Description

The outstanding requests metric is the fastest indicator that the ensemble cannot dequeue client operations quickly enough—usually CPU saturation, storage latency on txn logs, or a noisy neighbor client.

## Value

Stops coordinated services from timing out en masse when ZK request latency climbs.

## Implementation

Poll `mntr` every 10–30s; parse `zk_outstanding_requests`, `zk_avg_latency`, `zk_server_state`. Use dedicated monitoring user and firewall rules. Alert >1000 sustained 5 minutes (tune to cluster size).

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval out=tonumber(zk_outstanding_requests)
| where out > 1000
| timechart span=1m max(out) as outstanding by host
```

## Visualization

Line chart (outstanding), Gauge peak.

## References

- [ZooKeeper — Four letter words](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_4lw)
