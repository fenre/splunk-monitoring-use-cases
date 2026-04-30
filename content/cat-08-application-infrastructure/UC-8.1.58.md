<!-- AUTO-GENERATED from UC-8.1.58.json — DO NOT EDIT -->

---
id: "8.1.58"
title: "ZooKeeper Connection Count by Client IP"
status: "draft"
criticality: "medium"
splunkPillar: "Security"
---

# UC-8.1.58 · ZooKeeper Connection Count by Client IP

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Operational &middot; **Status:** Draft

*We use this to protect shared ensembles from accidental denial-of-service by one application release.*

---

## Description

A single client IP opening hundreds of sessions usually signals a connection leak or misconfigured pool, which can exhaust file descriptors and starve legitimate brokers.

## Value

Protects shared ensembles from accidental denial-of-service by one application release.

## Implementation

Whitelist `cons` in `zoo.cfg`; schedule read-only `cons` dumps to Splunk with sourcetype `zookeeper:conf` (rename if you prefer `zookeeper:cons`). Sanitize payloads; restrict index ACLs. Alternative: alert only on `zk_num_alive_connections` spikes from `mntr` when `cons` is disallowed.

## SPL

```spl
index=infrastructure sourcetype="zookeeper:conf"
| rex field=_raw "/(?<client_ip>\d+\.\d+\.\d+\.\d+):(?<client_port>\d+)"
| stats dc(client_port) as sessions by client_ip, host
| where sessions > 500
```

## Visualization

Table (client_ip, sessions), Bar chart top talkers.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [ZooKeeper — cons command](https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_cons)
