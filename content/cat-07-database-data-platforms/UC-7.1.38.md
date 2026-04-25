<!-- AUTO-GENERATED from UC-7.1.38.json — DO NOT EDIT -->

---
id: "7.1.38"
title: "Query Plan Regression (Runtime vs Baseline)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.38 · Query Plan Regression (Runtime vs Baseline)

## Description

Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

## Value

Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

## Implementation

Refresh baseline lookup weekly from stable period. Alert on regression >40% with new `plan_id`. Consider force plan workflow.

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: DB Connect, Query Store export.
• Ensure the following data sources are available: `sys.query_store_runtime_stats`, `dba_hist_sqlstat`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Refresh baseline lookup weekly from stable period. Alert on regression >40% with new `plan_id`. Consider force plan workflow.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:query_store_runtime"
| stats avg(avg_cpu_time) as cur_cpu by query_id, plan_id
| lookup query_baselines query_id OUTPUT baseline_cpu_ms
| eval regression_pct=round((cur_cpu-baseline_cpu_ms)/baseline_cpu_ms*100,1)
| where regression_pct > 40
```

Understanding this SPL

**Query Plan Regression (Runtime vs Baseline)** — Compares current average CPU/duration from Query Store or AWR to baselines by `query_id`/`plan_hash`. Tightens UC-7.1.14 with explicit baseline lookup.

Documented **Data sources**: `sys.query_store_runtime_stats`, `dba_hist_sqlstat`. **App/TA** (typical add-on context): DB Connect, Query Store export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:query_store_runtime. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:query_store_runtime". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by query_id, plan_id** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **regression_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where regression_pct > 40` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (regressed queries), Line chart (baseline vs current), Bar chart (regression %).

## SPL

```spl
index=database sourcetype="dbconnect:query_store_runtime"
| stats avg(avg_cpu_time) as cur_cpu by query_id, plan_id
| lookup query_baselines query_id OUTPUT baseline_cpu_ms
| eval regression_pct=round((cur_cpu-baseline_cpu_ms)/baseline_cpu_ms*100,1)
| where regression_pct > 40
```

## Visualization

Table (regressed queries), Line chart (baseline vs current), Bar chart (regression %).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
