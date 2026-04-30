<!-- AUTO-GENERATED from UC-7.4.20.json — DO NOT EDIT -->

---
id: "7.4.20"
title: "Cassandra Cluster Load per Node Trending"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.20 · Cassandra Cluster Load per Node Trending

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity &middot; **Status:** Draft

*We check backup and snapshot success and growth so we can trust restores and long-term storage plans for regulation and for real incidents.*

---

## Description

Uneven or rapidly growing load (storage) per Cassandra node signals compaction debt, partition skew, or backup residue—standard nodetool monitoring.

## Value

Helps rebalance before nodes hit disk watermarks and hints pile up.

## Implementation

Parse load as numeric bytes (strip human suffixes if present). Run daily max per node. Compare to trailing baseline; alert on skew between replicas of the same token range.

## SPL

```spl
index=database sourcetype="cassandra:nodetool_status"
| eval load_bytes=tonumber(replace(load,",",""))
| timechart span=1d max(load_bytes) as max_load by address, cluster_name
| streamstats window=7 avg(max_load) as baseline by address, cluster_name
| where max_load > baseline*1.3
```

## Visualization

Line chart (load by node), Bar chart (node skew ratio), Table (cluster, address, load).

## Known False Positives

Repairs, streaming, and hinted handoff create bursty patterns during normal cluster operations; use change windows and `nodetool` state for context.

## References

- [Apache Cassandra nodetool status](https://cassandra.apache.org/doc/latest/cassandra/tools/nodetool/status.html)
