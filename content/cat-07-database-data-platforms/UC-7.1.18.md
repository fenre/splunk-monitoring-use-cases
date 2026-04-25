<!-- AUTO-GENERATED from UC-7.1.18.json — DO NOT EDIT -->

---
id: "7.1.18"
title: "Long-Running Query and Blocking Session Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.18 · Long-Running Query and Blocking Session Detection

## Description

Queries that run for hours or sessions that block others cause timeouts and user impact. Identifying blocking chains and long-running queries supports tuning and kill decisions.

## Value

Queries that run for hours or sessions that block others cause timeouts and user impact. Identifying blocking chains and long-running queries supports tuning and kill decisions.

## Implementation

Poll active sessions and wait/block info. Ingest sessions with elapsed time >5 minutes or with blocking_session set. Alert on blocking chains. Dashboard top long-running and blocked sessions with SQL text.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; Oracle Enterprise Manager, SQLcl, or SQL Developer with `V$` views; psql, pgAdmin, or the managed-PostgreSQL console with `pg_stat_*` and replication views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: `splunk_app_db_connect`, database wait/block views.
• Ensure the following data sources are available: Oracle `V$SESSION`/`V$SQL`, PostgreSQL `pg_stat_activity`, SQL Server `sys.dm_exec_requests`/`sys.dm_os_waiting_tasks`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll active sessions and wait/block info. Ingest sessions with elapsed time >5 minutes or with blocking_session set. Alert on blocking chains. Dashboard top long-running and blocked sessions with SQL text.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| dbxquery connection="oracle_prod" query="SELECT s.sid, s.serial#, s.username, s.seconds_in_wait, s.blocking_session, sq.sql_text FROM v\$session s JOIN v\$sql sq ON s.sql_id=sq.sql_id WHERE s.seconds_in_wait > 300 OR s.blocking_session IS NOT NULL"
| table sid username seconds_in_wait blocking_session sql_text
```

Understanding this SPL

**Long-Running Query and Blocking Session Detection** — Queries that run for hours or sessions that block others cause timeouts and user impact. Identifying blocking chains and long-running queries supports tuning and kill decisions.

Documented **Data sources**: Oracle `V$SESSION`/`V$SQL`, PostgreSQL `pg_stat_activity`, SQL Server `sys.dm_exec_requests`/`sys.dm_os_waiting_tasks`. **App/TA** (typical add-on context): `splunk_app_db_connect`, database wait/block views. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Pipeline stage (see **Long-Running Query and Blocking Session Detection**): dbxquery connection="oracle_prod" query="SELECT s.sid, s.serial#, s.username, s.seconds_in_wait, s.blocking_session, sq.sql_text FROM v\$…
• Pipeline stage (see **Long-Running Query and Blocking Session Detection**): table sid username seconds_in_wait blocking_session sql_text


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (session, user, wait time, blocker), Blocking chain diagram, Line chart (long-running count).

## SPL

```spl
| dbxquery connection="oracle_prod" query="SELECT s.sid, s.serial#, s.username, s.seconds_in_wait, s.blocking_session, sq.sql_text FROM v\$session s JOIN v\$sql sq ON s.sql_id=sq.sql_id WHERE s.seconds_in_wait > 300 OR s.blocking_session IS NOT NULL"
| table sid username seconds_in_wait blocking_session sql_text
```

## Visualization

Table (session, user, wait time, blocker), Blocking chain diagram, Line chart (long-running count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
