<!-- AUTO-GENERATED from UC-7.1.9.json — DO NOT EDIT -->

---
id: "7.1.9"
title: "Index Fragmentation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.9 · Index Fragmentation

## Description

Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

## Value

Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

## Implementation

Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll index fragmentation stats via DB Connect weekly (resource-intensive query — schedule during off-hours). Alert when critical indexes exceed 30% fragmentation. Track fragmentation trend to optimize rebuild schedules.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```

Understanding this SPL

**Index Fragmentation** — Highly fragmented indexes cause excessive I/O and slow query performance. Monitoring guides maintenance scheduling.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (SQL Server), `pg_stat_user_indexes` (PostgreSQL). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:index_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where avg_fragmentation_pct > 30` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Index Fragmentation**): table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).

## SPL

```spl
index=database sourcetype="dbconnect:index_stats"
| where avg_fragmentation_pct > 30
| table server, database_name, table_name, index_name, avg_fragmentation_pct, page_count
| sort -avg_fragmentation_pct
```

## Visualization

Table (fragmented indexes), Bar chart (fragmentation by database), Heatmap (table × index fragmentation).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
