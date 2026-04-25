<!-- AUTO-GENERATED from UC-7.1.3.json — DO NOT EDIT -->

---
id: "7.1.3"
title: "Connection Pool Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.3 · Connection Pool Exhaustion

## Description

Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

## Value

Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

## Implementation

Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.

## Detailed Implementation

Prerequisites
• In operations we cross-check the same window in SQL Server Management Studio, Azure Data Studio, or the Azure SQL portal with `sys.dm_*` views; psql, pgAdmin, or the managed-PostgreSQL console with `pg_stat_*` and replication views so live metrics match what Splunk shows.
• Install and configure the required add-on or app: DB Connect, performance counters.
• Ensure the following data sources are available: SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll connection counts via DB Connect every 5 minutes. Compare against configured maximum. Alert at 80% and 95% thresholds. Track by application/user to identify connection leaks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```

Understanding this SPL

**Connection Pool Exhaustion** — Exhausted connection pools cause application failures. Monitoring prevents outages and guides pool sizing decisions.

Documented **Data sources**: SQL Server DMVs (`sys.dm_exec_connections`), PostgreSQL `pg_stat_activity`, app server connection pool metrics. **App/TA** (typical add-on context): DB Connect, performance counters. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:mssql_connections. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:mssql_connections". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct_used > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% connections used), Line chart (connections over time), Table (connections by application).

## SPL

```spl
index=database sourcetype="dbconnect:mssql_connections"
| timechart span=5m max(active_connections) as active, max(max_connections) as max_limit
| eval pct_used=round(active/max_limit*100,1)
| where pct_used > 80
```

## Visualization

Gauge (% connections used), Line chart (connections over time), Table (connections by application).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
