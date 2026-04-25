<!-- AUTO-GENERATED from UC-7.2.30.json — DO NOT EDIT -->

---
id: "7.2.30"
title: "Cassandra Inter-Node Streaming Progress (nodetool netstats)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.30 · Cassandra Inter-Node Streaming Progress (nodetool netstats)

## Description

During repair, rebuild, or add-node operations, streams that stall in WAITING with no byte progress often indicate network or disk issues—common Cassandra operational triage.

## Value

Reduces time to recover when topology changes hang mid-stream and client timeouts increase.

## Implementation

Parse netstats output into one event per stream direction. Poll every 2–5 minutes while operations are active. Suppress during approved maintenance. Correlate with nodetool compactionstats.

## SPL

```spl
index=database sourcetype="cassandra:netstats"
| where stream_state IN ("PREPARING","STREAMING","WAITING") OR receiving_bytes > 0 OR sending_bytes > 0
| eval stall=if(stream_state=="WAITING" AND receiving_bytes==0 AND sending_bytes==0,1,0)
| where stall==1
| stats count by peer, operation, host, cluster_name
```

## Visualization

Sankey or table (source→peer), Timeline (bytes/sec), Single value (stuck streams).

## References

- [Apache Cassandra nodetool netstats](https://cassandra.apache.org/doc/latest/cassandra/tools/nodetool/netstats.html)
