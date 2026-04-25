<!-- AUTO-GENERATED from UC-8.1.60.json — DO NOT EDIT -->

---
id: "8.1.60"
title: "ZooKeeper znode Count and Data Tree Growth"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.60 · ZooKeeper znode Count and Data Tree Growth

## Description

Runaway znode creation fills memory and lengthens snapshot times—common when automation misuses configuration paths or when consumers churn ephemeral parents inefficiently.

## Value

Prevents lengthy recovery and JVM pressure during snapshot and purge cycles.

## Implementation

Daily rollups reduce noise. Join with change calendar. Validate `zk_approximate_data_size` availability on your ZK release.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval nodes=tonumber(zk_znode_count)
| eval bytes=tonumber(zk_approximate_data_size)
| bin _time span=1d
| stats latest(nodes) as znodes latest(bytes) as approx_bytes by host, _time
| streamstats window=30 global=f delta(znodes) as node_growth by host
| where node_growth > 100000 OR approx_bytes > 10737418240
```

## Visualization

Line chart (znodes), Area chart (approx_bytes).

## References

- [ZooKeeper Admin — quotas](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_zkCommands)
