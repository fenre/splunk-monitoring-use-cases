<!-- AUTO-GENERATED from UC-7.5.4.json — DO NOT EDIT -->

---
id: "7.5.4"
title: "OpenSearch Search Latency"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.4 · OpenSearch Search Latency

## Description

P95/P99 query latency directly affects application UX; separating queue time from query time narrows tuning to thread pools vs. mappings and shards.

## Value

P95/P99 query latency directly affects application UX; separating queue time from query time narrows tuning to thread pools vs. mappings and shards.

## Implementation

Ingest node-level search metrics (`primaries.search.query_time_in_millis` / `query_total`) for derived latency, and/or enable slow search logging and forward with a dedicated sourcetype. Baseline p95 per cluster; alert when p95 exceeds threshold for 15+ minutes. Correlate with heap GC and segment merges.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom scripted input (`_nodes/stats` search, slow log), OpenSearch slow search log.
• Ensure the following data sources are available: `sourcetype=opensearch:search_latency`, `sourcetype=opensearch:slowlog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest node-level search metrics (`primaries.search.query_time_in_millis` / `query_total`) for derived latency, and/or enable slow search logging and forward with a dedicated sourcetype. Baseline p95 per cluster; alert when p95 exceeds threshold for 15+ minutes. Correlate with heap GC and segment merges.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="opensearch:search_latency" OR sourcetype="opensearch:slowlog"
| eval took_ms=coalesce(took_ms, took)
| where took_ms > 500
| timechart span=5m perc95(took_ms) as p95_ms, perc99(took_ms) as p99_ms by cluster_name
```

Understanding this SPL

**OpenSearch Search Latency** — P95/P99 query latency directly affects application UX; separating queue time from query time narrows tuning to thread pools vs. mappings and shards.

Documented **Data sources**: `sourcetype=opensearch:search_latency`, `sourcetype=opensearch:slowlog`. **App/TA** (typical add-on context): Custom scripted input (`_nodes/stats` search, slow log), OpenSearch slow search log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: opensearch:search_latency, opensearch:slowlog. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="opensearch:search_latency". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **took_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where took_ms > 500` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by cluster_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p95/p99 search latency), Table (slow queries from slowlog), Histogram of `took_ms`.

## SPL

```spl
index=database sourcetype="opensearch:search_latency" OR sourcetype="opensearch:slowlog"
| eval took_ms=coalesce(took_ms, took)
| where took_ms > 500
| timechart span=5m perc95(took_ms) as p95_ms, perc99(took_ms) as p99_ms by cluster_name
```

## Visualization

Line chart (p95/p99 search latency), Table (slow queries from slowlog), Histogram of `took_ms`.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
