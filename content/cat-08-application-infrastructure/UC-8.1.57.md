<!-- AUTO-GENERATED from UC-8.1.57.json — DO NOT EDIT -->

---
id: "8.1.57"
title: "ZooKeeper Snapshot and Transaction Log Size Growth"
status: "draft"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-8.1.57 · ZooKeeper Snapshot and Transaction Log Size Growth

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Capacity &middot; **Status:** Draft

*We watch for signs that avoids emergency purges and extended downtime when txn logs or snapshots consume the data volume.*

---

## Description

Sharp growth in approximate data size or znode footprint usually precedes full disks on `dataDir`/`dataLogDir` and longer snapshot cycles—both extend recovery time after failures.

## Value

Avoids emergency purges and extended downtime when txn logs or snapshots consume the data volume.

## Implementation

Poll `mntr` hourly for trend; add `df` or Prometheus `node_filesystem_size_bytes` for the volumes backing txn logs and snapshots. When alerts fire, verify `autopurge.snapRetainCount` / `snapCount` and that snapshots complete (check `zookeeper:log` for snapshot messages).

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval approx=tonumber(zk_approximate_data_size)
| eval nodes=tonumber(zk_znode_count)
| bin _time span=1h
| stats latest(approx) as approx_bytes latest(nodes) as znodes by host, _time
| streamstats window=24 global=f last(approx_bytes) as _prev_bytes_per_hour by host
| eval bytes_per_hour = approx_bytes - _prev_bytes_per_hour| where bytes_per_hour > 1073741824 OR approx_bytes > 5368709120
```

## Visualization

Line chart (approx_bytes, bytes_per_hour), Table (host).

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [ZooKeeper — Data directory](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_dataDir)
