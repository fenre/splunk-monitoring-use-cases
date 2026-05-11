<!-- AUTO-GENERATED from UC-7.1.70.json — DO NOT EDIT -->

---
id: "7.1.70"
title: "Cassandra Gossip and Ring Membership State Changes"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.70 · Cassandra Gossip and Ring Membership State Changes

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Change &middot; **Status:** Draft

*We watch Cassandra Gossip and Ring Membership State Changes so we can keep this part of the data platform within the capacity and quality targets our teams expect.*

---

## Description

Frequent gossip transitions often foreshadow split-brain risk, misrouted replicas, or rolling restarts gone wrong. Correlating bursts with deployment windows separates healthy operations from instability.

## Value

Protects data consistency and query availability by catching ring instability before client drivers see repeated timeouts.

## Implementation

Ingest `system.log` with correct timezone; tag `cluster_name` via `inputs.conf` `_meta`. Create allowlist for expected rolling restart patterns. Join with CMDB for rack awareness. Escalate when events spike outside change windows.

## SPL

```spl
index=database sourcetype="cassandra:system"
| search ("GossipStage" OR "InetAddress" OR "Node.*state" OR "FailureDetector") AND ("removed" OR "down" OR "UP" OR "LEFT" OR "shutdown")
| rex field=_raw "(?<peer_ip>\d+\.\d+\.\d+\.\d+)"
| bin _time span=1m
| stats count as state_events dc(peer_ip) as peers_affected by host, _time
| where state_events > 20
```

## Visualization

Timeline (state_events), Table (host, peers_affected), Node diagram optional with enrichment.

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [Apache Cassandra — Gossip](https://cassandra.apache.org/doc/latest/cassandra/architecture/)
