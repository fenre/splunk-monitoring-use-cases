<!-- AUTO-GENERATED from UC-7.1.31.json — DO NOT EDIT -->

---
id: "7.1.31"
title: "SQL Server Always On AG Health and Replica Sync"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.31 · SQL Server Always On AG Health and Replica Sync

## Description

Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

## Value

Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

## Implementation

Poll DMVs every 5m. Alert on unhealthy sync or queue >100MB (tune threshold). Track automatic failover readiness.

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: DB Connect, `Splunk_TA_microsoft-sqlserver`.
• Ensure the following data sources are available: `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll DMVs every 5m. Alert on unhealthy sync or queue >100MB (tune threshold). Track automatic failover readiness.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:ag_replica_state"
| where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600
| table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size
```

Understanding this SPL

**SQL Server Always On AG Health and Replica Sync** — Combined view of `synchronization_health`, redo queue, and log send queue sizes for AG replicas. Operationalizes UC-7.1.12 with queue depth.

Documented **Data sources**: `sys.dm_hadr_database_replica_states`, `log_send_queue_size`, `redo_queue_size`. **App/TA** (typical add-on context): DB Connect, `Splunk_TA_microsoft-sqlserver`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:ag_replica_state. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:ag_replica_state". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **SQL Server Always On AG Health and Replica Sync**): table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (replica × health), Line chart (queue sizes), Table (unhealthy AG databases).

## SPL

```spl
index=database sourcetype="dbconnect:ag_replica_state"
| where synchronization_health_desc!="HEALTHY" OR log_send_queue_size > 104857600 OR redo_queue_size > 104857600
| table ag_name replica_server_name synchronization_health_desc log_send_queue_size redo_queue_size
```

## Visualization

Status grid (replica × health), Line chart (queue sizes), Table (unhealthy AG databases).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
