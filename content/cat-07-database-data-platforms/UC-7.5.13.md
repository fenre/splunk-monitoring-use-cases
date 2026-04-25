<!-- AUTO-GENERATED from UC-7.5.13.json — DO NOT EDIT -->

---
id: "7.5.13"
title: "Elasticsearch Search Latency and Slow Queries"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.13 · Elasticsearch Search Latency and Slow Queries

## Description

Search latency trending detects degradation before users notice. Slow log analysis identifies expensive queries for optimization.

## Value

Search latency trending detects degradation before users notice. Slow log analysis identifies expensive queries for optimization.

## Implementation

Poll `GET _nodes/stats/indices/search` to compute per-node average query latency from cumulative counters. Enable slow logs (`index.search.slowlog.threshold.query.warn: 5s`) and forward to Splunk. Correlate slow queries with specific indices and query patterns. Alert on sustained average latency above baseline or frequent slow log entries.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats`), Elasticsearch slow logs forwarded to Splunk.
• Ensure the following data sources are available: `sourcetype=elasticsearch:search_stats`, `sourcetype=elasticsearch:slow_log`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/indices/search` to compute per-node average query latency from cumulative counters. Enable slow logs (`index.search.slowlog.threshold.query.warn: 5s`) and forward to Splunk. Correlate slow queries with specific indices and query patterns. Alert on sustained average latency above baseline or frequent slow log entries.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:search_stats"
| eval query_latency_ms=search.query_time_in_millis/search.query_total
| timechart span=5m avg(query_latency_ms) as avg_latency_ms, max(query_latency_ms) as p100_latency_ms by node_name
| where avg_latency_ms > 500
```

Understanding this SPL

**Elasticsearch Search Latency and Slow Queries** — Search latency trending detects degradation before users notice. Slow log analysis identifies expensive queries for optimization.

Documented **Data sources**: `sourcetype=elasticsearch:search_stats`, `sourcetype=elasticsearch:slow_log`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats`), Elasticsearch slow logs forwarded to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:search_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:search_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **query_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where avg_latency_ms > 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (query latency p50/p95/p100), Table (slow queries by index), Single value (current avg latency).

## SPL

```spl
index=database sourcetype="elasticsearch:search_stats"
| eval query_latency_ms=search.query_time_in_millis/search.query_total
| timechart span=5m avg(query_latency_ms) as avg_latency_ms, max(query_latency_ms) as p100_latency_ms by node_name
| where avg_latency_ms > 500
```

## Visualization

Line chart (query latency p50/p95/p100), Table (slow queries by index), Single value (current avg latency).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
