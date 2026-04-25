<!-- AUTO-GENERATED from UC-7.1.6.json — DO NOT EDIT -->

---
id: "7.1.6"
title: "Backup Success Verification"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.6 · Backup Success Verification

## Description

Database backups are the last line of defense. Verifying success prevents discovering backup failures during a crisis.

## Value

Database backups are the last line of defense. Verifying success prevents discovering backup failures during a crisis.

## Implementation

Query backup history tables via DB Connect daily. Alert on any database without a successful backup in the expected window. Cross-reference with CMDB for backup classification (full/diff/log) requirements.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: DB Connect, Splunk_TA_microsoft-sqlserver.
• Ensure the following data sources are available: `msdb.dbo.backupset` (SQL Server), `v$rman_backup_job_details` (Oracle), PostgreSQL `pg_basebackup` logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query backup history tables via DB Connect daily. Alert on any database without a successful backup in the expected window. Cross-reference with CMDB for backup classification (full/diff/log) requirements.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:backup_history"
| stats latest(backup_finish_date) as last_backup, latest(type) as backup_type by database_name, server_name
| eval hours_since=round((now()-strptime(last_backup,"%Y-%m-%d %H:%M:%S"))/3600,1)
| where hours_since > 24
| table server_name, database_name, last_backup, backup_type, hours_since
```

Understanding this SPL

**Backup Success Verification** — Database backups are the last line of defense. Verifying success prevents discovering backup failures during a crisis.

Documented **Data sources**: `msdb.dbo.backupset` (SQL Server), `v$rman_backup_job_details` (Oracle), PostgreSQL `pg_basebackup` logs. **App/TA** (typical add-on context): DB Connect, Splunk_TA_microsoft-sqlserver. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:backup_history. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:backup_history". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by database_name, server_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **hours_since** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hours_since > 24` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Backup Success Verification**): table server_name, database_name, last_backup, backup_type, hours_since


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (databases with backup status), Single value (databases missing backup), Status grid (database × backup type).

## SPL

```spl
index=database sourcetype="dbconnect:backup_history"
| stats latest(backup_finish_date) as last_backup, latest(type) as backup_type by database_name, server_name
| eval hours_since=round((now()-strptime(last_backup,"%Y-%m-%d %H:%M:%S"))/3600,1)
| where hours_since > 24
| table server_name, database_name, last_backup, backup_type, hours_since
```

## Visualization

Table (databases with backup status), Single value (databases missing backup), Status grid (database × backup type).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
