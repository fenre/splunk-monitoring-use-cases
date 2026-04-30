<!-- AUTO-GENERATED from UC-7.2.26.json — DO NOT EDIT -->

---
id: "7.2.26"
title: "ZooKeeper Quorum Follower Sync Gap"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.26 · ZooKeeper Quorum Follower Sync Gap

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Status:** Draft

*We watch ZooKeeper Quorum Follower Sync Gap so we can keep this part of the data platform within the capacity and quality targets our teams expect.*

---

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

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [Apache ZooKeeper — The Four Letter Words (mntr)](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_zkCommands)
