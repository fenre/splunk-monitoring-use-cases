<!-- AUTO-GENERATED from UC-7.1.51.json — DO NOT EDIT -->

---
id: "7.1.51"
title: "MongoDB Sharded Cluster Chunk Migration Failures"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.51 · MongoDB Sharded Cluster Chunk Migration Failures

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Operations &middot; **Status:** Draft

*We watch for repeated or suspicious sign-in activity on our databases so we can catch brute-force and misconfiguration before they become account takeovers.*

---

## Description

Failed chunk migrations leave jumbo chunks, hot shards, and incomplete balancing; applications see uneven latency and capacity risk on a single shard. Detecting repeated migration failures early prevents outages when one shard becomes the only write path.

## Value

Gives the platform team time to fix network partitions, disk space, or config metadata issues before customer-facing latency spikes and shard exhaustion.

## Implementation

Forward `mongos` and config server logs to Splunk; assign `mongodb:log` in `props.conf` with correct `TIME_FORMAT` for your MongoDB log version. Tag `host` with mongos identity. Create a correlation lookup for approved maintenance windows. Alert when three or more failure signatures occur within five minutes per namespace.

## SPL

```spl
index=database sourcetype="mongodb:log"
| search ("FailedToStartChunkMigration" OR "migration failed" OR "moveChunk failed" OR "ChunkMigrationFailed")
| rex field=message "ns:\s+(?<ns>[^\s]+)"
| bin _time span=5m
| stats count as failures values(message) as samples by host, ns, _time
| where failures >= 3
```

## Visualization

Timeline (failures over time), Table (host, ns, failures, sample message), Map (shard host roles if enriched).

## Known False Positives

Yellow or relocating shards during rolling restarts, ILM/ISM moves, or snapshot restore; compare with maintenance before treating as an incident.

## References

- [MongoDB — sharding chunk migration](https://www.mongodb.com/docs/manual/core/sharding-balancer-administration/)
- [MongoDB log messages reference](https://www.mongodb.com/docs/manual/reference/log-messages/)
