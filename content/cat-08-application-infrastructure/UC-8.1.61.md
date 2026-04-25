<!-- AUTO-GENERATED from UC-8.1.61.json — DO NOT EDIT -->

---
id: "8.1.61"
title: "ZooKeeper Quorum Role and ruok Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-8.1.61 · ZooKeeper Quorum Role and ruok Health

## Description

When `ruok` stops returning `imok`, the JVM may be wedged even though the process exists—dependent systems should fail over or stop sending traffic before sessions die.

## Value

Shortens detection path versus waiting for client session expirations across the estate.

## Implementation

Run checks from two vantage points to avoid false positives. Pair with `zookeeper:mntr` `zk_server_state` for leader awareness. Do not expose four-letter ports publicly.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:ruok"
| eval healthy=if(match(_raw,"imok") OR response="imok",1,0)
| bin _time span=1m
| stats min(healthy) as ok by host, _time
| where ok=0
```

## Visualization

Single value (ensemble health), Timeline (failures).

## References

- [ZooKeeper — ruok](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_zkCommands)
