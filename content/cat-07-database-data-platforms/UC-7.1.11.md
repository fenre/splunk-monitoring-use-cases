<!-- AUTO-GENERATED from UC-7.1.11.json — DO NOT EDIT -->

---
id: "7.1.11"
title: "Buffer Cache Hit Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.11 · Buffer Cache Hit Ratio

## Description

Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

## Value

Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

## Implementation

Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: DB Connect, performance counters.
• Ensure the following data sources are available: SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll buffer cache performance counters via DB Connect every 15 minutes. Alert when hit ratio drops below 95% for sustained periods. Correlate with memory pressure and query workload changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```

Understanding this SPL

**Buffer Cache Hit Ratio** — Low buffer cache hit ratio means excessive disk I/O. Monitoring guides memory allocation decisions.

Documented **Data sources**: SQL Server performance counters, PostgreSQL `pg_stat_bgwriter`. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:perf_counters. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:perf_counters". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where counter_name="Buffer cache hit ratio"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by instance_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where hit_ratio < 95` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).

## SPL

```spl
index=database sourcetype="dbconnect:perf_counters"
| where counter_name="Buffer cache hit ratio"
| timechart span=15m avg(cntr_value) as hit_ratio by instance_name
| where hit_ratio < 95
```

## Visualization

Gauge (buffer cache hit ratio), Line chart (hit ratio over time), Single value (current hit ratio %).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
