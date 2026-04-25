<!-- AUTO-GENERATED from UC-7.4.4.json — DO NOT EDIT -->

---
id: "7.4.4"
title: "Credit / Cost per Query"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.4 · Credit / Cost per Query

## Description

Directly ties compute cost to individual queries, enabling chargeback and cost optimization. Identifies runaway queries consuming excessive resources.

## Value

Directly ties compute cost to individual queries, enabling chargeback and cost optimization. Identifies runaway queries consuming excessive resources.

## Implementation

Poll query history with cost metrics daily. Calculate cost per query, per user, and per team (using role mapping). Create weekly cost report. Alert on individual queries exceeding cost threshold. Set up warehouse-level budgets.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Custom API input (Snowflake ACCOUNT_USAGE).
• Ensure the following data sources are available: Snowflake `QUERY_HISTORY` (CREDITS_USED), BigQuery `INFORMATION_SCHEMA.JOBS` (total_bytes_billed).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll query history with cost metrics daily. Calculate cost per query, per user, and per team (using role mapping). Create weekly cost report. Alert on individual queries exceeding cost threshold. Set up warehouse-level budgets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval cost=CREDITS_USED_CLOUD_SERVICES * 3
| stats sum(cost) as total_cost, count as query_count by USER_NAME, WAREHOUSE_NAME
| eval cost_per_query=round(total_cost/query_count,2)
| sort -total_cost
```

Understanding this SPL

**Credit / Cost per Query** — Directly ties compute cost to individual queries, enabling chargeback and cost optimization. Identifies runaway queries consuming excessive resources.

Documented **Data sources**: Snowflake `QUERY_HISTORY` (CREDITS_USED), BigQuery `INFORMATION_SCHEMA.JOBS` (total_bytes_billed). **App/TA** (typical add-on context): Custom API input (Snowflake ACCOUNT_USAGE). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: snowflake:query_history. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="snowflake:query_history". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **cost** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by USER_NAME, WAREHOUSE_NAME** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **cost_per_query** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (cost by user/warehouse), Table (most expensive queries), Line chart (daily cost trend), Pie chart (cost by team).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval cost=CREDITS_USED_CLOUD_SERVICES * 3
| stats sum(cost) as total_cost, count as query_count by USER_NAME, WAREHOUSE_NAME
| eval cost_per_query=round(total_cost/query_count,2)
| sort -total_cost
```

## Visualization

Bar chart (cost by user/warehouse), Table (most expensive queries), Line chart (daily cost trend), Pie chart (cost by team).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
