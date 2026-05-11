<!-- AUTO-GENERATED from UC-7.1.32.json — DO NOT EDIT -->

---
id: "7.1.32"
title: "Database Backup Chain Validation"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.32 · Database Backup Chain Validation

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We check backup and snapshot success and growth so we can trust restores and long-term storage plans for regulation and for real incidents.*

---

## Description

Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

## Value

Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

## Implementation

Custom SQL to flag LSN gaps. For Oracle, check archivelog sequence continuity. Alert on any break in chain for production databases.

## Detailed Implementation

### Prerequisites
- In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
- Install and configure the required add-on or app: DB Connect, backup vendor logs.
- Ensure the following data sources are available: `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Custom SQL to flag LSN gaps. For Oracle, check archivelog sequence continuity. Alert on any break in chain for production databases.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:backup_chain"
| sort database_name, backup_finish_date
| streamstats window=2 previous(last_lsn) as prev_last by database_name
| where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1
| table database_name backup_finish_date type first_lsn prev_last
```

#### Understanding this SPL

**Database Backup Chain Validation** — Verifies full→diff→log chain continuity (SQL Server LSN chain, Oracle archivelog sequence) to detect missing backups before restore drills fail.

Documented **Data sources**: `msdb.dbo.backupset` (first_lsn, last_lsn, type), RMAN backup pieces. **App/TA** (typical add-on context): DB Connect, backup vendor logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:backup_chain. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=database, sourcetype="dbconnect:backup_chain". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- `streamstats` rolls up events into metrics; results are split **by database_name** so each row reflects one combination of those dimensions.
- Filters the current rows with `where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1` — typically the threshold or rule expression for this monitoring goal.
- Pipeline stage (see **Database Backup Chain Validation**): table database_name backup_finish_date type first_lsn prev_last


### Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (broken chains), Timeline (backup types), Single value (databases with gaps).

## SPL

```spl
index=database sourcetype="dbconnect:backup_chain"
| sort database_name, backup_finish_date
| streamstats window=2 last(last_lsn) as prev_last by database_name
| where isnotnull(prev_last) AND first_lsn!=prev_last AND type!=1
| table database_name backup_finish_date type first_lsn prev_last
```

## Visualization

Table (broken chains), Timeline (backup types), Single value (databases with gaps).

## Known False Positives

Planned full or differential backups, log backup bursts, and restore drills can spike I/O and job duration; suppress or threshold against the known backup window.

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
