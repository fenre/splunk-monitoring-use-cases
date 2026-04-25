<!-- AUTO-GENERATED from UC-7.1.67.json — DO NOT EDIT -->

---
id: "7.1.67"
title: "Cassandra Compaction Backlog and Pending Tasks"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.67 · Cassandra Compaction Backlog and Pending Tasks

## Description

A monotonically growing pending compaction count means the node cannot rewrite SSTables fast enough for the write load, which soon shows up as read latency and repair failures. Early detection avoids disk-full and timeout incidents during peak traffic.

## Value

Keeps OLTP and analytics paths on Cassandra responsive by triggering throttling, compaction strategy reviews, or capacity adds before timeouts cascade.

## Implementation

Run `nodetool compactionstats` every 60–120s via scripted input; parse `pending tasks`, `id`, `keyspace`, `table`, `progress`, `total`. Alternatively enable JMX `CompactionExecutor` pending metric via TA-JMX `inputs.conf` with `sourcetype=cassandra:compaction`. Baseline per cluster class; suppress during repairs via maintenance lookup.

## SPL

```spl
index=database sourcetype="cassandra:compaction"
| eval pending=tonumber(pending_tasks)
| where pending > 100
| bin _time span=15m
| stats max(pending) as max_pending latest(bytes_total_in_progress) as bytes_in_progress by host, cluster_name, _time
| where max_pending > 150
```

## Visualization

Line chart (max_pending), Table (keyspace, table, bytes_in_progress).

## References

- [Apache Cassandra — compaction](https://cassandra.apache.org/doc/latest/cassandra/operating/compaction/index.html)
- [Splunk Add-on for JMX](https://splunkbase.splunk.com/app/2647)
