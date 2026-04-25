<!-- AUTO-GENERATED from UC-8.1.54.json — DO NOT EDIT -->

---
id: "8.1.54"
title: "ZooKeeper Follower Sync Lag vs Quorum Leader"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.54 · ZooKeeper Follower Sync Lag vs Quorum Leader

## Description

When the leader reports fewer synced followers than quorum size or rising pending syncs, new proposals are at risk and read-after-write consistency degrades for sensitive clients.

## Value

Prevents split-brain-like symptoms in stacks that assume strong ZK session semantics during failures.

## Implementation

Only leader nodes emit follower counts—filter `zk_server_state` in parser. Poll frequently during changes. Join with `zookeeper:ruok` health checks. Alert when lag persists >2 polling intervals.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval followers=tonumber(zk_followers)
| eval synced=tonumber(zk_synced_followers)
| eval pending=tonumber(zk_pending_syncs)
| eval lag=followers-synced
| where zk_server_state="leader" AND (lag>0 OR pending>10)
| table _time, host, followers, synced, pending, lag
```

## Visualization

Line chart (synced vs followers), Single value (pending syncs).

## References

- [ZooKeeper Admin Guide](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html)
