<!-- AUTO-GENERATED from UC-8.1.59.json — DO NOT EDIT -->

---
id: "8.1.59"
title: "ZooKeeper Ephemeral ZNode Count Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.59 · ZooKeeper Ephemeral ZNode Count Trending

## Description

Ephemeral nodes track live service registrations; abnormal growth can mean stuck clients, failed session teardown, or registry bugs—each increases memory and watch traffic.

## Value

Keeps service-discovery load predictable for microservices and Kafka controllers alike.

## Implementation

Baseline weekly seasonality. Correlate with deploys. If ephemeral counts fall suddenly, investigate mass session loss separately.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:mntr"
| eval ephem=tonumber(zk_ephemerals_count)
| bin _time span=1h
| stats latest(ephem) as ephemeral_count by host, _time
| streamstats window=168 global=f median(ephemeral_count) as med_eph by host
| where ephemeral_count > med_eph*1.5 AND ephemeral_count > 50000
```

## Visualization

Line chart (ephemeral_count vs median), Table (host).

## References

- [ZooKeeper — Ephemeral nodes](https://zookeeper.apache.org/doc/current/zookeeperProgrammers.html#sc_ephemeralZnodes)
