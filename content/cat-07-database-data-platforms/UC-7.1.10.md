<!-- AUTO-GENERATED from UC-7.1.10.json — DO NOT EDIT -->

---
id: "7.1.10"
title: "TempDB Contention (SQL Server)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.10 · TempDB Contention (SQL Server)

## Description

TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

## Value

TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

## Implementation

Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver.
• Ensure the following data sources are available: `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll wait statistics via DB Connect. Filter for PAGELATCH waits on TempDB (database_id 2). Alert when TempDB waits exceed baseline. Recommend adding TempDB data files equal to number of CPU cores (up to 8).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```

Understanding this SPL

**TempDB Contention (SQL Server)** — TempDB contention is a common SQL Server bottleneck. Detection enables configuration tuning (multiple data files, trace flags).

Documented **Data sources**: `sys.dm_os_wait_stats` (PAGELATCH waits), `sys.dm_exec_query_stats`. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:wait_stats. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:wait_stats". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by wait_type** so each row reflects one combination of those dimensions.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).

## SPL

```spl
index=database sourcetype="dbconnect:wait_stats"
| where wait_type LIKE "PAGELATCH%" AND resource_description LIKE "2:%"
| stats sum(wait_time_ms) as total_wait by wait_type
```

## Visualization

Bar chart (wait types), Line chart (TempDB wait trend), Single value (current TempDB wait ms).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
