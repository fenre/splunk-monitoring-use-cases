<!-- AUTO-GENERATED from UC-7.1.39.json — DO NOT EDIT -->

---
id: "7.1.39"
title: "Database Patch Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.39 · Database Patch Compliance

## Description

Compares instance `@@VERSION` / `banner` / Oracle `DBA_REGISTRY_HISTORY` to approved patch levels per environment. Supports security patching SLAs.

## Value

Compares instance `@@VERSION` / `banner` / Oracle `DBA_REGISTRY_HISTORY` to approved patch levels per environment. Supports security patching SLAs.

## Implementation

Maintain `approved_db_patch` lookup (engine, major, approved CU/RU). Daily compare. Alert on non-compliant production instances.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views; psql, pgAdmin, or the managed-PostgreSQL console with `pg_stat_*` and replication views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect, inventory scripted input.
• Ensure the following data sources are available: SQL Server `@@VERSION`, Oracle `opatch`, PostgreSQL `pg_version`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain `approved_db_patch` lookup (engine, major, approved CU/RU). Daily compare. Alert on non-compliant production instances.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:instance_version"
| lookup approved_db_patch matrix_key OUTPUT approved_build
| where build != approved_build
| table host, engine, build, approved_build, last_patch_date
```

Understanding this SPL

**Database Patch Compliance** — Compares instance `@@VERSION` / `banner` / Oracle `DBA_REGISTRY_HISTORY` to approved patch levels per environment. Supports security patching SLAs.

Documented **Data sources**: SQL Server `@@VERSION`, Oracle `opatch`, PostgreSQL `pg_version`. **App/TA** (typical add-on context): DB Connect, inventory scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:instance_version. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:instance_version". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where build != approved_build` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Database Patch Compliance**): table host, engine, build, approved_build, last_patch_date


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (non-compliant hosts), Pie chart (compliant %), Single value (drift count).

## SPL

```spl
index=database sourcetype="dbconnect:instance_version"
| lookup approved_db_patch matrix_key OUTPUT approved_build
| where build != approved_build
| table host, engine, build, approved_build, last_patch_date
```

## Visualization

Table (non-compliant hosts), Pie chart (compliant %), Single value (drift count).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
