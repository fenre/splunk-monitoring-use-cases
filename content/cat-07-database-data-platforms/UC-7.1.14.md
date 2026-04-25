<!-- AUTO-GENERATED from UC-7.1.14.json — DO NOT EDIT -->

---
id: "7.1.14"
title: "Query Plan Regression"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.14 · Query Plan Regression

## Description

Query plan changes can cause sudden performance degradation. Detection enables rapid intervention (plan forcing, hint application).

## Value

Query plan changes can cause sudden performance degradation. Detection enables rapid intervention (plan forcing, hint application).

## Implementation

Enable Query Store on SQL Server databases. Poll query performance metrics via DB Connect. Maintain baseline lookup of normal query durations. Alert when queries regress >50% from baseline. Enable automatic plan correction if available.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: SQL Server Query Store, `sys.dm_exec_query_plan`, PostgreSQL `pg_stat_statements`; lookup `query_baselines.csv` with columns `query_id, baseline_avg` (rolling 30-day median rebuilt nightly).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Query Store on SQL Server databases. Poll query performance metrics via DB Connect. Maintain baseline lookup of normal query durations. Alert when queries regress >50% from baseline. Enable automatic plan correction if available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:query_store"
| stats avg(avg_duration) as current_avg by query_id, plan_id
| lookup query_baselines.csv query_id OUTPUT baseline_avg
| where isnotnull(baseline_avg) AND baseline_avg > 0
| eval regression_pct=round((current_avg-baseline_avg)/baseline_avg*100,1)
| where regression_pct > 50
```

Understanding this SPL

**Query Plan Regression** — Query plan changes can cause sudden performance degradation. Detection enables rapid intervention (plan forcing, hint application).

Documented **Data sources**: SQL Server Query Store, `sys.dm_exec_query_plan`, PostgreSQL `pg_stat_statements`; lookup `query_baselines.csv` with columns `query_id, baseline_avg` (rolling 30-day median rebuilt nightly). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:query_store. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:query_store". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by query_id, plan_id** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where isnotnull(baseline_avg) AND baseline_avg > 0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **regression_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where regression_pct > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (regressed queries), Bar chart (regression % by query), Line chart (query duration trend).

## SPL

```spl
index=database sourcetype="dbconnect:query_store"
| stats avg(avg_duration) as current_avg by query_id, plan_id
| lookup query_baselines.csv query_id OUTPUT baseline_avg
| where isnotnull(baseline_avg) AND baseline_avg > 0
| eval regression_pct=round((current_avg-baseline_avg)/baseline_avg*100,1)
| where regression_pct > 50
```

## Visualization

Table (regressed queries), Bar chart (regression % by query), Line chart (query duration trend).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
