<!-- AUTO-GENERATED from UC-7.2.25.json — DO NOT EDIT -->

---
id: "7.2.25"
title: "Cassandra Node Down or Unreachable (nodetool status)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.25 · Cassandra Node Down or Unreachable (nodetool status)

## Description

Operational states other than UN in nodetool status indicate down, joining, or moving nodes. This is the first-line availability check in Cassandra runbooks.

## Value

Triggers rapid incident response before quorum loss, hinted handoff backlog, and read/write availability degradation.

## Implementation

Run nodetool status every 1–2 minutes per cluster; emit one event per node with normalized state codes. Exclude intentional decommission windows via maintenance lookup. Pair with cassandra:compactionstats and streaming metrics.

## SPL

```spl
index=database sourcetype="cassandra:nodetool_status"
| where state IN ("DN","DL","DS")
| stats latest(state) as state latest(load) as load by address, datacenter, rack, cluster_name
| sort state
```

## Visualization

Table (node, state, DC), Single value (non-UN nodes), Timeline (state transitions).

## References

- [Apache Cassandra nodetool status](https://cassandra.apache.org/doc/latest/cassandra/tools/nodetool/status.html)
