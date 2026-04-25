<!-- AUTO-GENERATED from UC-7.1.30.json — DO NOT EDIT -->

---
id: "7.1.30"
title: "Oracle Tablespace Growth Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.30 · Oracle Tablespace Growth Trending

## Description

Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

## Value

Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

## Implementation

Daily snapshot. Alert on >10GB/week growth on critical tablespaces. Use `predict` on used_bytes for runway to maxsize.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Daily snapshot. Alert on >10GB/week growth on critical tablespaces. Use `predict` on used_bytes for runway to maxsize.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| timechart span=1d latest(USED_SPACE) as used_bytes by TABLESPACE_NAME
| streamstats window=7 range(used_bytes) as growth_7d by TABLESPACE_NAME
| eval growth_gb=round(growth_7d/1073741824,2)
| where growth_gb > 10
```

Understanding this SPL

**Oracle Tablespace Growth Trending** — Week-over-week growth rate per tablespace drives forecast and ASM/space procurement. Extends point-in-time utilization with trend.

Documented **Data sources**: `DBA_TABLESPACE_USAGE_METRICS` (used_space, tablespace_size). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:oracle_tablespace. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:oracle_tablespace". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by TABLESPACE_NAME** — ideal for trending and alerting on this use case.
• `streamstats` rolls up events into metrics; results are split **by TABLESPACE_NAME** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **growth_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where growth_gb > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (used GB trend), Table (tablespace, growth GB/week), Single value (fastest growing).

## SPL

```spl
index=database sourcetype="dbconnect:oracle_tablespace"
| timechart span=1d latest(USED_SPACE) as used_bytes by TABLESPACE_NAME
| streamstats window=7 range(used_bytes) as growth_7d by TABLESPACE_NAME
| eval growth_gb=round(growth_7d/1073741824,2)
| where growth_gb > 10
```

## Visualization

Line chart (used GB trend), Table (tablespace, growth GB/week), Single value (fastest growing).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
