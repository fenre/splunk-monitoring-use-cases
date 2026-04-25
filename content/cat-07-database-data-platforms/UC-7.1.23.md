<!-- AUTO-GENERATED from UC-7.1.23.json — DO NOT EDIT -->

---
id: "7.1.23"
title: "PostgreSQL Vacuum Activity"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.23 · PostgreSQL Vacuum Activity

## Description

Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

## Value

Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

## Implementation

Poll `pg_stat_user_tables` via DB Connect every hour. Extract `n_dead_tup`, `n_live_tup`, `last_autovacuum`. Compute dead tuple ratio and time since last vacuum. Alert when dead_ratio >5% or n_dead_tup >10000 for critical tables. Alert when last_autovacuum is >24 hours for high-churn tables. Track autovacuum runs from `pg_stat_progress_vacuum` if available.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Splunk DB Connect or custom scripted input.
• Ensure the following data sources are available: `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `pg_stat_user_tables` via DB Connect every hour. Extract `n_dead_tup`, `n_live_tup`, `last_autovacuum`. Compute dead tuple ratio and time since last vacuum. Alert when dead_ratio >5% or n_dead_tup >10000 for critical tables. Alert when last_autovacuum is >24 hours for high-churn tables. Track autovacuum runs from `pg_stat_progress_vacuum` if available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:pg_stat_user_tables"
| eval dead_ratio=round(n_dead_tup/nullif(n_live_tup,0)*100, 2)
| where dead_ratio > 5 OR n_dead_tup > 10000
| eval hours_since_vacuum=round((now()-strptime(last_autovacuum,"%Y-%m-%d %H:%M:%S"))/3600, 1)
| table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
| sort -n_dead_tup
```

Understanding this SPL

**PostgreSQL Vacuum Activity** — Autovacuum running, dead tuples, and table bloat affect query performance. Monitoring ensures vacuum keeps pace with write workload and prevents bloat.

Documented **Data sources**: `pg_stat_user_tables` (n_dead_tup, n_live_tup, last_autovacuum, last_vacuum). **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:pg_stat_user_tables. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:pg_stat_user_tables". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dead_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dead_ratio > 5 OR n_dead_tup > 10000` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **hours_since_vacuum** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **PostgreSQL Vacuum Activity**): table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (tables with bloat risk), Bar chart (dead tuples by table), Line chart (dead tuple ratio trend), Single value (tables overdue for vacuum).

## SPL

```spl
index=database sourcetype="dbconnect:pg_stat_user_tables"
| eval dead_ratio=round(n_dead_tup/nullif(n_live_tup,0)*100, 2)
| where dead_ratio > 5 OR n_dead_tup > 10000
| eval hours_since_vacuum=round((now()-strptime(last_autovacuum,"%Y-%m-%d %H:%M:%S"))/3600, 1)
| table schemaname, relname, n_dead_tup, n_live_tup, dead_ratio, last_autovacuum, hours_since_vacuum
| sort -n_dead_tup
```

## Visualization

Table (tables with bloat risk), Bar chart (dead tuples by table), Line chart (dead tuple ratio trend), Single value (tables overdue for vacuum).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
