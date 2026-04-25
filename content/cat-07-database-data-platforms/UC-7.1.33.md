<!-- AUTO-GENERATED from UC-7.1.33.json — DO NOT EDIT -->

---
id: "7.1.33"
title: "Long-Running Query Detection (Active Sessions)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.33 · Long-Running Query Detection (Active Sessions)

## Description

Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

## Value

Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

## Implementation

Poll every 2m. Exclude known batch accounts via lookup. Alert when max_sec >900 for OLTP. Include optional `sql_text` sampling for compliance.

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll every 2m. Exclude known batch accounts via lookup. Alert when max_sec >900 for OLTP. Include optional `sql_text` sampling for compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:active_requests"
| where elapsed_sec > 300 AND status="running"
| stats max(elapsed_sec) as max_sec by session_id, database_name, sql_hash
| table session_id database_name sql_hash max_sec wait_type
```

Understanding this SPL

**Long-Running Query Detection (Active Sessions)** — Surfaces currently running queries exceeding elapsed threshold with SQL hash and wait type—faster triage than transaction-only UC-7.1.8.

Documented **Data sources**: `sys.dm_exec_requests`, `pg_stat_activity`, `V$SESSION` + `V$SQL`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:active_requests. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:active_requests". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where elapsed_sec > 300 AND status="running"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by session_id, database_name, sql_hash** so each row reflects one combination of those dimensions.
• Pipeline stage (see **Long-Running Query Detection (Active Sessions)**): table session_id database_name sql_hash max_sec wait_type


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (long-running sessions), Line chart (count of long queries), Single value (longest elapsed sec).

## SPL

```spl
index=database sourcetype="dbconnect:active_requests"
| where elapsed_sec > 300 AND status="running"
| stats max(elapsed_sec) as max_sec by session_id, database_name, sql_hash
| table session_id database_name sql_hash max_sec wait_type
```

## Visualization

Table (long-running sessions), Line chart (count of long queries), Single value (longest elapsed sec).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
