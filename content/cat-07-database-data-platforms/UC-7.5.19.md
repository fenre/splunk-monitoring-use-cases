<!-- AUTO-GENERATED from UC-7.5.19.json — DO NOT EDIT -->

---
id: "7.5.19"
title: "Elasticsearch Segment Merge Pressure"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.5.19 · Elasticsearch Segment Merge Pressure

## Description

Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

## Value

Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

## Implementation

Poll `GET _nodes/stats/indices/merges` for `current`, `total_size_in_bytes`, `total_time_in_millis`, and `total_throttled_time_in_millis`. Compute merge rate and throttle ratio. Alert when active merges remain high (>3) for sustained periods, or when throttle time exceeds 50% of total merge time. Correlate with indexing rate and search latency to detect I/O contention.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/indices/merges`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:merge_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/indices/merges` for `current`, `total_size_in_bytes`, `total_time_in_millis`, and `total_throttled_time_in_millis`. Compute merge rate and throttle ratio. Alert when active merges remain high (>3) for sustained periods, or when throttle time exceeds 50% of total merge time. Correlate with indexing rate and search latency to detect I/O contention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:merge_stats"
| eval merge_rate_mb=merges.total_size_in_bytes/1048576
| timechart span=5m avg(merges.current) as active_merges, sum(merge_rate_mb) as merge_mb by node_name
| where active_merges > 3
```

Understanding this SPL

**Elasticsearch Segment Merge Pressure** — Heavy segment merge activity competes with search for disk I/O, causing latency spikes. Merge throttling slows indexing. Monitoring merge pressure helps balance indexing throughput against search performance.

Documented **Data sources**: `sourcetype=elasticsearch:merge_stats`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/indices/merges`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:merge_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:merge_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **merge_rate_mb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where active_merges > 3` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (active merges over time), Stacked area (merge vs. throttle time), Single value (current merge count).

## SPL

```spl
index=database sourcetype="elasticsearch:merge_stats"
| eval merge_rate_mb=merges.total_size_in_bytes/1048576
| timechart span=5m avg(merges.current) as active_merges, sum(merge_rate_mb) as merge_mb by node_name
| where active_merges > 3
```

## Visualization

Line chart (active merges over time), Stacked area (merge vs. throttle time), Single value (current merge count).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
