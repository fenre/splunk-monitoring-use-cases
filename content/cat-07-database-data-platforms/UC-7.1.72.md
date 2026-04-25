<!-- AUTO-GENERATED from UC-7.1.72.json — DO NOT EDIT -->

---
id: "7.1.72"
title: "Cassandra SSTable Count per Table"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.72 · Cassandra SSTable Count per Table

## Description

An unusually high live SSTable count increases read amplification and slows compactions on LCS/STCS tables. Finding outliers versus peer median isolates nodes needing repair, cleanup, or compaction tuning.

## Value

Prevents gradual read latency erosion on wide partitions and large tables without waiting for user-facing timeouts.

## Implementation

Map `SSTable count` (or `Live SSTables`) to `sstable_count` in your parser. Run weekly full snapshots and hourly for top-N tables. Exclude secondary index tables via lookup. When alerting, include `nodetool compactionstats` link in runbook.

## SPL

```spl
index=database sourcetype="cassandra:nodetool_cfstats"
| eval sstables=tonumber(sstable_count)
| where sstables > 100
| stats max(sstables) as max_sstables by keyspace_name, table_name, host
| eventstats median(max_sstables) as cluster_median by keyspace_name, table_name
| where max_sstables > cluster_median*2
| sort -max_sstables
```

## Visualization

Bar chart (max_sstables by table), Table (host outliers).

## References

- [Apache Cassandra — SSTables](https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html)
