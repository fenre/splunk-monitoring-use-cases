<!-- AUTO-GENERATED from UC-7.1.69.json — DO NOT EDIT -->

---
id: "7.1.69"
title: "Cassandra Tombstone Warnings on Read Path"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.69 · Cassandra Tombstone Warnings on Read Path

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Data Quality &middot; **Status:** Draft

*We surface slow and blocking queries so we can fix the worst offenders first and keep applications and batch jobs within the response times we promise.*

---

## Description

Reads that cross large numbers of tombstones slow every replica and can trigger GC storms; log warnings are the fastest signal that TTL, delete patterns, or compaction are misaligned with access paths.

## Value

Avoids surprise latency incidents during batch deletes or TTL changes and guides data modeling fixes before timeouts dominate.

## Implementation

Set `props.conf` `LINE_BREAKER` for multiline stack traces; extract `keyspace` and `table` via `EXTRACT-cassandra_table`. Tune `tombstone_warn_threshold` awareness—alerts should fire below catastrophic defaults. Pair with `cassandra:nodetool_cfstats` `Droppable tombstone` metrics.

## SPL

```spl
index=database sourcetype="cassandra:system"
| search "tombstone" AND ("WARN" OR "ERROR" OR "ReadCommand")
| rex field=_raw "Read (?<read_type>\w+) query.* scanned (?<scanned>\d+) tombstones.* limit (?<limit>\d+)"
| eval over_limit=if(scanned>limit,1,0)
| stats count as warn_events max(scanned) as max_tombstones by keyspace, table, host
| where warn_events >= 5 OR max_tombstones > 10000
```

## Visualization

Timeline (warn_events), Table (keyspace, table, max_tombstones).

## Known False Positives

Planned failovers, network maintenance, or heavy bulk replication can extend lag for a time without an outage; align the alert with the DR runbook and change window.

## References

- [Apache Cassandra — Tombstones](https://cassandra.apache.org/doc/latest/cassandra/developing/cql/dml.html#deletes)
