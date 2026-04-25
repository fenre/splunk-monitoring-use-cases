<!-- AUTO-GENERATED from UC-7.1.12.json — DO NOT EDIT -->

---
id: "7.1.12"
title: "Database Availability Group Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.12 · Database Availability Group Health

## Description

AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

## Value

AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

## Implementation

Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver.
• Ensure the following data sources are available: `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll AG replica state DMVs every 5 minutes. Alert on any non-HEALTHY or non-CONNECTED state. Track failover events from SQL Server error log. Create dashboard showing full AG topology and health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```

Understanding this SPL

**Database Availability Group Health** — AG/RAC cluster health is essential for HA. Detecting unhealthy replicas prevents unplanned failover failures.

Documented **Data sources**: `sys.dm_hadr_availability_replica_states` (SQL Server), Oracle CRS logs. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:ag_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:ag_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Database Availability Group Health**): table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).

## SPL

```spl
index=database sourcetype="dbconnect:ag_status"
| where synchronization_health_desc!="HEALTHY" OR connected_state_desc!="CONNECTED"
| table _time, ag_name, replica_server_name, role_desc, synchronization_health_desc
```

## Visualization

Status grid (replica × health state), Table (unhealthy replicas), Timeline (failover events).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
