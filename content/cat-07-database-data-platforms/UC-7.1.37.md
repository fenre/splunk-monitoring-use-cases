<!-- AUTO-GENERATED from UC-7.1.37.json — DO NOT EDIT -->

---
id: "7.1.37"
title: "Temp Tablespace Usage (Oracle TEMP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.37 · Temp Tablespace Usage (Oracle TEMP)

## Description

High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

## Value

High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

## Implementation

Poll `V$TEMPSEG_USAGE` every 5m. Alert at 85% of temp max. Identify top SQL by `sql_id` from same view.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect.
• Ensure the following data sources are available: `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `V$TEMPSEG_USAGE` every 5m. Alert at 85% of temp max. Identify top SQL by `sql_id` from same view.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:oracle_temp"
| stats sum(blocks_used) as used_blocks by tablespace_name, session_addr
| eventstats sum(used_blocks) as total_used by tablespace_name
| lookup oracle_temp_space tablespace_name OUTPUT max_blocks
| where total_used > max_blocks*0.85
| table tablespace_name total_used max_blocks
```

Understanding this SPL

**Temp Tablespace Usage (Oracle TEMP)** — High `TEMP` usage for sorts and hashes causes ORA-1652. Tracks session temp consumption vs temp tablespace limits.

Documented **Data sources**: `V$TEMPSEG_USAGE`, `DBA_TEMP_FREE_SPACE`. **App/TA** (typical add-on context): DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:oracle_temp. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:oracle_temp". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by tablespace_name, session_addr** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by tablespace_name** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where total_used > max_blocks*0.85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Temp Tablespace Usage (Oracle TEMP)**): table tablespace_name total_used max_blocks


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (temp usage %), Table (sessions using temp), Single value (peak temp GB).

## SPL

```spl
index=database sourcetype="dbconnect:oracle_temp"
| stats sum(blocks_used) as used_blocks by tablespace_name, session_addr
| eventstats sum(used_blocks) as total_used by tablespace_name
| lookup oracle_temp_space tablespace_name OUTPUT max_blocks
| where total_used > max_blocks*0.85
| table tablespace_name total_used max_blocks
```

## Visualization

Line chart (temp usage %), Table (sessions using temp), Single value (peak temp GB).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
