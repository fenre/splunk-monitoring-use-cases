<!-- AUTO-GENERATED from UC-7.1.35.json — DO NOT EDIT -->

---
id: "7.1.35"
title: "Connection Pool Exhaustion (Application vs Database Limit)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.35 · Connection Pool Exhaustion (Application vs Database Limit)

## Description

Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

## Value

Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

## Implementation

Ingest both sides; use `transaction` or `join` on host+service. Alert when either side >90%. Dashboard side-by-side.

## Detailed Implementation

Prerequisites
• In operations we confirm in the right vendor console (OEM, SSMS, pgAdmin, MySQL Workbench, mongosh) for the engine the SPL actually targets.
• Install and configure the required add-on or app: OpenTelemetry, DB Connect.
• Ensure the following data sources are available: HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest both sides; use `transaction` or `join` on host+service. Alert when either side >90%. Dashboard side-by-side.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="hikaricp:metrics"
| eval pct=round(active_connections/max_connections*100,1)
| where pct > 90 OR threads_awaiting_connection > 5
| table host pool_name pct threads_awaiting_connection active_connections max_connections
```

Understanding this SPL

**Connection Pool Exhaustion (Application vs Database Limit)** — Joins app pool `activeThreads`/`waiting` with DB `session_count` to distinguish app-side pool starvation from DB `max_connections` hits.

Documented **Data sources**: HikariCP metrics, `pg_stat_activity` count, `sys.dm_exec_connections`. **App/TA** (typical add-on context): OpenTelemetry, DB Connect. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: hikaricp:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="hikaricp:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct > 90 OR threads_awaiting_connection > 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Connection Pool Exhaustion (Application vs Database Limit)**): table host pool_name pct threads_awaiting_connection active_connections max_connections


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (app pool vs DB sessions), Line chart (pct over time), Table (hosts in danger).

## SPL

```spl
index=application sourcetype="hikaricp:metrics"
| eval pct=round(active_connections/max_connections*100,1)
| where pct > 90 OR threads_awaiting_connection > 5
| table host pool_name pct threads_awaiting_connection active_connections max_connections
```

## Visualization

Gauge (app pool vs DB sessions), Line chart (pct over time), Table (hosts in danger).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
