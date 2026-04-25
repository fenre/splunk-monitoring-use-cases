<!-- AUTO-GENERATED from UC-7.1.13.json — DO NOT EDIT -->

---
id: "7.1.13"
title: "Schema Change Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.13 · Schema Change Detection

## Description

Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

## Value

Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

## Implementation

Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; psql, pgAdmin, or the managed-PostgreSQL console with `pg_stat_*` and replication views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect, SQL Server audit.
• Ensure the following data sources are available: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable SQL Server audit for DDL events (CREATE, ALTER, DROP). For PostgreSQL, set `log_statement='ddl'`. Forward audit logs to Splunk. Alert on any DDL outside maintenance windows. Correlate with change tickets.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```

Understanding this SPL

**Schema Change Detection** — Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

Documented **Data sources**: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mssql:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mssql:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Schema Change Detection**): table _time, server_principal_name, database_name, object_name, statement
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action, All_Changes.object span=1h | sort - count
```

Understanding this CIM / accelerated SPL

**Schema Change Detection** — Unauthorized DDL changes to production databases can break applications. Detection ensures change control compliance.

Documented **Data sources**: SQL Server DDL triggers, audit logs, PostgreSQL `log_statement='ddl'`. **App/TA** (typical add-on context): DB Connect, SQL Server audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).

## SPL

```spl
index=database sourcetype="mssql:audit" action_id IN ("CR","AL","DR")
| table _time, server_principal_name, database_name, object_name, statement
| sort -_time
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Change.All_Changes by All_Changes.user, All_Changes.action, All_Changes.object span=1h | sort - count
```

## Visualization

Table (DDL events with details), Timeline (schema changes), Bar chart (changes by user).

## References

- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
