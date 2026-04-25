<!-- AUTO-GENERATED from UC-7.1.1.json — DO NOT EDIT -->

---
id: "7.1.1"
title: "Slow Query Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.1 · Slow Query Detection

## Description

Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

## Value

Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

## Implementation

Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.

## Detailed Implementation

Prerequisites
• In operations we confirm in MySQL Workbench, Percona Monitoring and Management, or the managed-MySQL cloud console alongside Splunk.
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log.
• Ensure the following data sources are available: Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable MySQL slow query log (long_query_time=5). For SQL Server, poll DMVs via DB Connect. For PostgreSQL, enable `pg_stat_statements`. Ingest and alert on queries exceeding thresholds. Report top offenders weekly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```

Understanding this SPL

**Slow Query Detection** — Slow queries at the P95/P99 level directly impact checkout, search, and reporting latency, hitting revenue and SLA commitments. They also hold locks and inflate CPU/IO, degrading performance for other tenants and queries. Prioritize fixes by business-critical endpoint and wait type, not just raw query duration.

Documented **Data sources**: Slow query logs, SQL Server DMVs (`sys.dm_exec_query_stats`), PostgreSQL `pg_stat_statements`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver, MySQL slow query log. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mysql:slowquery. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mysql:slowquery". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where query_time > 5` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by db, user** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).

## SPL

```spl
index=database sourcetype="mysql:slowquery"
| rex field=_raw "Query_time:\s+(?<query_time>[\d.]+)"
| where query_time > 5
| stats count, avg(query_time) as avg_time by db, user
| sort -avg_time
```

## Visualization

Table (slow queries with details), Bar chart (top slow queries by avg duration), Line chart (slow query count trend).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
