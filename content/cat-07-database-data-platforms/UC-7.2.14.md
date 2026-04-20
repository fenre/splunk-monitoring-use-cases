---
id: "7.2.14"
title: "Cassandra Compaction Backlog and Throughput"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.14 · Cassandra Compaction Backlog and Throughput

## Description

Pending compactions and compaction throughput indicate whether the cluster keeps up with writes. Complements generic compaction UC with nodetool-derived rates.

## Value

Pending compactions and compaction throughput indicate whether the cluster keeps up with writes. Complements generic compaction UC with nodetool-derived rates.

## Implementation

Poll nodetool every 5m per node. Alert when pending_tasks grows monotonically for 1h or throughput collapses.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: JMX, `nodetool compactionstats` scripted input.
• Ensure the following data sources are available: `pending_tasks`, `bytes_compacted`, `compaction throughput`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll nodetool every 5m per node. Alert when pending_tasks grows monotonically for 1h or throughput collapses.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="cassandra:compactionstats"
| where pending_tasks > 100 OR compaction_throughput_mbps < 5
| timechart span=15m max(pending_tasks) as pending, avg(compaction_throughput_mbps) as tp_mbps by cluster_name
```

Understanding this SPL

**Cassandra Compaction Backlog and Throughput** — Pending compactions and compaction throughput indicate whether the cluster keeps up with writes. Complements generic compaction UC with nodetool-derived rates.

Documented **Data sources**: `pending_tasks`, `bytes_compacted`, `compaction throughput`. **App/TA** (typical add-on context): JMX, `nodetool compactionstats` scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: cassandra:compactionstats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="cassandra:compactionstats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where pending_tasks > 100 OR compaction_throughput_mbps < 5` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by cluster_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-axis (pending vs throughput), Table (nodes with backlog), Line chart (pending tasks).

## SPL

```spl
index=database sourcetype="cassandra:compactionstats"
| where pending_tasks > 100 OR compaction_throughput_mbps < 5
| timechart span=15m max(pending_tasks) as pending, avg(compaction_throughput_mbps) as tp_mbps by cluster_name
```

## Visualization

Dual-axis (pending vs throughput), Table (nodes with backlog), Line chart (pending tasks).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
