<!-- AUTO-GENERATED from UC-8.1.53.json — DO NOT EDIT -->

---
id: "8.1.53"
title: "ZooKeeper Leader Election Frequency"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.1.53 · ZooKeeper Leader Election Frequency

## Description

Frequent leader elections indicate unstable quorum members or clock skew and stall writes across every dependent system. Detecting election storms early avoids hours of mysterious client timeouts.

## Value

Stabilizes metadata services for Kafka and Hadoop during network maintenance or storage events.

## Implementation

Tune log verbosity to capture state changes without drowning indexes. Deduplicate rolling restarts via maintenance lookup. Correlate with `zookeeper:stat` output for zxid jumps.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:log"
| search "LEADING" OR "FOLLOWING" OR "LOOKING" OR "leader election"
| rex field=_raw "(?<zk_role>LEADING|FOLLOWING|LOOKING)"
| bin _time span=10m
| stats dc(zk_role) as role_changes count as lines by host, _time
| where role_changes >= 3 OR match(_raw,"(?i)election")
```

## Visualization

Timeline (election keywords), Table (host, role_changes).

## References

- [ZooKeeper — Quorum](https://zookeeper.apache.org/doc/current/zookeeperInternals.html)
