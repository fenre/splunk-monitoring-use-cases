<!-- AUTO-GENERATED from UC-7.2.26.json — DO NOT EDIT -->

---
id: "7.2.26"
title: "ZooKeeper Quorum Follower Sync Gap"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.26 · ZooKeeper Quorum Follower Sync Gap

## Description

When zk_synced_followers lags zk_followers, part of the ensemble is not caught up—often precursing split-brain risk or dependent service outages (Kafka, ClickHouse, HBase).

## Value

Gives early warning before Kafka controller churn or ClickHouse replica read-only transitions caused by ensemble instability.

## Implementation

Poll mntr on each ZooKeeper peer. Parse integers for zk_followers and zk_synced_followers. Skip or branch standalone nodes. Alert when gap > 0 for more than two consecutive polls. Correlate with latency and outstanding_requests.

## SPL

```spl
index=zookeeper sourcetype="zookeeper:mntr"
| where isnotnull(zk_followers) AND zk_followers > 0
| eval follower_gap=zk_followers-zk_synced_followers
| where follower_gap > 0 OR zk_synced_followers < zk_followers
| timechart span=5m max(follower_gap) as unsynced_followers by host
```

## Visualization

Line chart (follower gap), Table (ensemble host, followers, synced), Single value (gap).

## References

- [Apache ZooKeeper — The Four Letter Words (mntr)](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_zkCommands)
