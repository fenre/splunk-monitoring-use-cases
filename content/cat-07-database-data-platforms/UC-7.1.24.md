<!-- AUTO-GENERATED from UC-7.1.24.json — DO NOT EDIT -->

---
id: "7.1.24"
title: "PostgreSQL Connection Pool Monitoring (PgBouncer)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.24 · PostgreSQL Connection Pool Monitoring (PgBouncer)

## Description

Pool utilization and wait queue length indicate connection pressure. High utilization or growing wait queue causes application timeouts.

## Value

Pool utilization and wait queue length indicate connection pressure. High utilization or growing wait queue causes application timeouts.

## Implementation

Create a scripted input that connects to PgBouncer admin console (default port 6432) and runs `SHOW POOLS` and `SHOW STATS` every 5 minutes. Parse output into structured events. Extract `cl_active`, `cl_wait`, `max_client_conn` per database/pool. Alert when pool utilization >80% or `cl_wait` >5. Track `sv_idle`, `sv_used` for server connection usage.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Custom scripted input (PgBouncer SHOW POOLS/STATS).
• Ensure the following data sources are available: PgBouncer admin console output (`SHOW POOLS`, `SHOW STATS`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a scripted input that connects to PgBouncer admin console (default port 6432) and runs `SHOW POOLS` and `SHOW STATS` every 5 minutes. Parse output into structured events. Extract `cl_active`, `cl_wait`, `max_client_conn` per database/pool. Alert when pool utilization >80% or `cl_wait` >5. Track `sv_idle`, `sv_used` for server connection usage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="pgbouncer:pools"
| eval pool_util_pct=round(cl_active+cl_wait)/nullif(max_client_conn,0)*100, 1
| eval wait_queue=cl_wait
| where pool_util_pct > 80 OR wait_queue > 5
| timechart span=5m max(pool_util_pct) as util_pct, max(wait_queue) as wait_queue by database, pool_mode
```

Understanding this SPL

**PostgreSQL Connection Pool Monitoring (PgBouncer)** — Pool utilization and wait queue length indicate connection pressure. High utilization or growing wait queue causes application timeouts.

Documented **Data sources**: PgBouncer admin console output (`SHOW POOLS`, `SHOW STATS`). **App/TA** (typical add-on context): Custom scripted input (PgBouncer SHOW POOLS/STATS). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: pgbouncer:pools. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="pgbouncer:pools". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pool_util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **wait_queue** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pool_util_pct > 80 OR wait_queue > 5` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by database, pool_mode** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (pool utilization %), Line chart (active vs wait connections), Table (pools with high utilization or wait queue).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=database sourcetype="pgbouncer:pools"
| eval pool_util_pct=round(cl_active+cl_wait)/nullif(max_client_conn,0)*100, 1
| eval wait_queue=cl_wait
| where pool_util_pct > 80 OR wait_queue > 5
| timechart span=5m max(pool_util_pct) as util_pct, max(wait_queue) as wait_queue by database, pool_mode
```

## Visualization

Gauge (pool utilization %), Line chart (active vs wait connections), Table (pools with high utilization or wait queue).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
