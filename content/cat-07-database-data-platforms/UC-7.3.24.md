<!-- AUTO-GENERATED from UC-7.3.24.json — DO NOT EDIT -->

---
id: "7.3.24"
title: "ZooKeeper Client Session Expiry Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.24 · ZooKeeper Client Session Expiry Events

## Description

Bursts of session expirations indicate GC pauses, network partitions, or mis-tuned session timeouts on clients such as Kafka brokers or HBase region servers.

## Value

Predicts cascading leader elections and dependent service outages by surfacing ensemble health from the authoritative server log.

## Implementation

Ensure ZooKeeper logs include session IDs. Deduplicate INFO vs WARN levels. Baseline per environment—Kafka clusters may spike during broker restarts. Correlate with JVM GC logs on ZooKeeper peers.

## SPL

```spl
index=zookeeper sourcetype="zookeeper:log"
| search ("Expiring session" OR "expired session" OR "Session.*expired")
| bin _time span=15m
| stats count as expired_sessions by host, _time
| where expired_sessions > 5
```

## Visualization

Timeline (expired sessions), Table (host, count), Single value (15m rate).

## References

- [ZooKeeper Programmer's Guide — Sessions](https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html#ch_zkSessions)
