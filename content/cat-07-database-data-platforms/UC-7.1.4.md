<!-- AUTO-GENERATED from UC-7.1.4.json — DO NOT EDIT -->

---
id: "7.1.4"
title: "Replication Lag Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.4 · Replication Lag Monitoring

## Description

Replication lag affects data consistency and failover readiness. Monitoring ensures HA/DR objectives are met.

## Value

Replication lag affects data consistency and failover readiness. Monitoring ensures HA/DR objectives are met.

## Implementation

Poll replication status via DB Connect at 5-minute intervals. Alert when lag exceeds RPO (e.g., >60 seconds). Track lag trend over time. Correlate spikes with batch jobs or network events.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: DB Connect, vendor-specific monitoring.
• Ensure the following data sources are available: SQL Server AG DMVs (`sys.dm_hadr_database_replica_states`), MySQL `SHOW SLAVE STATUS`, PostgreSQL replication slots.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll replication status via DB Connect at 5-minute intervals. Alert when lag exceeds RPO (e.g., >60 seconds). Track lag trend over time. Correlate spikes with batch jobs or network events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:replication_status"
| eval lag_seconds=coalesce(seconds_behind_master, replication_lag_sec)
| timechart span=5m max(lag_seconds) as max_lag by replica_name
| where max_lag > 60
```

Understanding this SPL

**Replication Lag Monitoring** — Replication lag affects data consistency and failover readiness. Monitoring ensures HA/DR objectives are met.

Documented **Data sources**: SQL Server AG DMVs (`sys.dm_hadr_database_replica_states`), MySQL `SHOW SLAVE STATUS`, PostgreSQL replication slots. **App/TA** (typical add-on context): DB Connect, vendor-specific monitoring. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:replication_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:replication_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_seconds** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by replica_name** — ideal for trending and alerting on this use case.
• Filters the current rows with `where max_lag > 60` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (lag over time by replica), Single value (current max lag), Table (replicas with lag status).

## SPL

```spl
index=database sourcetype="dbconnect:replication_status"
| eval lag_seconds=coalesce(seconds_behind_master, replication_lag_sec)
| timechart span=5m max(lag_seconds) as max_lag by replica_name
| where max_lag > 60
```

## Visualization

Line chart (lag over time by replica), Single value (current max lag), Table (replicas with lag status).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
