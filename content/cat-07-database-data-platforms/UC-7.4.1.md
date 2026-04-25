<!-- AUTO-GENERATED from UC-7.4.1.json — DO NOT EDIT -->

---
id: "7.4.1"
title: "Query Performance Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.1 · Query Performance Trending

## Description

Identifies expensive and slow queries impacting warehouse performance and cost. Enables query optimization and cost reduction.

## Value

Identifies expensive and slow queries impacting warehouse performance and cost. Enables query optimization and cost reduction.

## Implementation

Poll query history views via REST API or DB Connect daily. Track query duration, queue time, and cost. Identify top resource consumers. Create weekly optimization report for data engineering teams.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: Custom API input (Snowflake ACCOUNT_USAGE), DB Connect.
• Ensure the following data sources are available: Snowflake `QUERY_HISTORY`, BigQuery `INFORMATION_SCHEMA.JOBS`, Redshift `STL_QUERY`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll query history views via REST API or DB Connect daily. Track query duration, queue time, and cost. Identify top resource consumers. Create weekly optimization report for data engineering teams.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| where EXECUTION_STATUS="SUCCESS" AND TOTAL_ELAPSED_TIME > 60000
| stats avg(TOTAL_ELAPSED_TIME) as avg_ms, sum(CREDITS_USED_CLOUD_SERVICES) as credits by USER_NAME, WAREHOUSE_NAME
| sort -credits
```

Understanding this SPL

**Query Performance Trending** — Identifies expensive and slow queries impacting warehouse performance and cost. Enables query optimization and cost reduction.

Documented **Data sources**: Snowflake `QUERY_HISTORY`, BigQuery `INFORMATION_SCHEMA.JOBS`, Redshift `STL_QUERY`. **App/TA** (typical add-on context): Custom API input (Snowflake ACCOUNT_USAGE), DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:query_history. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="snowflake:query_history". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where EXECUTION_STATUS="SUCCESS" AND TOTAL_ELAPSED_TIME > 60000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by USER_NAME, WAREHOUSE_NAME** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (expensive queries), Bar chart (cost/duration by warehouse), Line chart (query performance trend).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| where EXECUTION_STATUS="SUCCESS" AND TOTAL_ELAPSED_TIME > 60000
| stats avg(TOTAL_ELAPSED_TIME) as avg_ms, sum(CREDITS_USED_CLOUD_SERVICES) as credits by USER_NAME, WAREHOUSE_NAME
| sort -credits
```

## Visualization

Table (expensive queries), Bar chart (cost/duration by warehouse), Line chart (query performance trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
