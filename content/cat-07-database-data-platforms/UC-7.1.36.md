<!-- AUTO-GENERATED from UC-7.1.36.json — DO NOT EDIT -->

---
id: "7.1.36"
title: "Index Fragmentation Maintenance Priority"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.36 · Index Fragmentation Maintenance Priority

## Description

Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

## Value

Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

## Implementation

Weekly job. Export top 50 for DBA runbook. Exclude tiny indexes via page_count floor.

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Weekly job. Export top 50 for DBA runbook. Exclude tiny indexes via page_count floor.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:index_stats"
| eval priority_score=avg_fragmentation_pct * page_count / 1000000
| where avg_fragmentation_pct > 30 AND page_count > 1000
| sort -priority_score
| head 50
```

Understanding this SPL

**Index Fragmentation Maintenance Priority** — Ranks indexes by fragmentation × page_count to schedule rebuilds during maintenance windows. Extends UC-7.1.9 with prioritization score.

Documented **Data sources**: `sys.dm_db_index_physical_stats` (avg_fragmentation_in_percent, page_count). **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:index_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:index_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **priority_score** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_fragmentation_pct > 30 AND page_count > 1000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (index, frag %, pages, score), Bar chart (top priority_score).

## SPL

```spl
index=database sourcetype="dbconnect:index_stats"
| eval priority_score=avg_fragmentation_pct * page_count / 1000000
| where avg_fragmentation_pct > 30 AND page_count > 1000
| sort -priority_score
| head 50
```

## Visualization

Table (index, frag %, pages, score), Bar chart (top priority_score).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
