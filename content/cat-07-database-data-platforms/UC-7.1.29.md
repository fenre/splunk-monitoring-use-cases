<!-- AUTO-GENERATED from UC-7.1.29.json — DO NOT EDIT -->

---
id: "7.1.29"
title: "MySQL InnoDB Buffer Pool Hit Ratio Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.1.29 · MySQL InnoDB Buffer Pool Hit Ratio Monitoring

## Description

Fleet-wide buffer pool hit ratio SLO for MySQL/MariaDB with per-instance drilldown. Aligns capacity reviews with read IO pressure.

## Value

Fleet-wide buffer pool hit ratio SLO for MySQL/MariaDB with per-instance drilldown. Aligns capacity reviews with read IO pressure.

## Implementation

Aggregate hourly for executive view; retain per-host series for alerts. Correlate drops with large table scans or buffer pool size changes.

## Detailed Implementation

Prerequisites
• In operations we confirm in MySQL Workbench, Percona Monitoring and Management, or the managed-MySQL cloud console alongside Splunk.
• Install and configure the required add-on or app: DB Connect, `SHOW GLOBAL STATUS`.
• Ensure the following data sources are available: `Innodb_buffer_pool_read_requests`, `Innodb_buffer_pool_reads`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Aggregate hourly for executive view; retain per-host series for alerts. Correlate drops with large table scans or buffer pool size changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)),2)
| bin _time span=1h
| stats avg(hit_ratio) as fleet_avg, min(hit_ratio) as worst by, _time
| where fleet_avg < 99 OR worst < 95
```

Understanding this SPL

**MySQL InnoDB Buffer Pool Hit Ratio Monitoring** — Fleet-wide buffer pool hit ratio SLO for MySQL/MariaDB with per-instance drilldown. Aligns capacity reviews with read IO pressure.

Documented **Data sources**: `Innodb_buffer_pool_read_requests`, `Innodb_buffer_pool_reads`. **App/TA** (typical add-on context): DB Connect, `SHOW GLOBAL STATUS`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:mysql_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:mysql_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• Filters the current rows with `where fleet_avg < 99 OR worst < 95` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (fleet avg vs worst instance), Gauge (current hit ratio), Table (instances below 99%).

## SPL

```spl
index=database sourcetype="dbconnect:mysql_status"
| eval hit_ratio=round(100*(1-Innodb_buffer_pool_reads/nullif(Innodb_buffer_pool_read_requests,0)),2)
| bin _time span=1h
| stats avg(hit_ratio) as fleet_avg, min(hit_ratio) as worst by, _time
| where fleet_avg < 99 OR worst < 95
```

## Visualization

Line chart (fleet avg vs worst instance), Gauge (current hit ratio), Table (instances below 99%).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
