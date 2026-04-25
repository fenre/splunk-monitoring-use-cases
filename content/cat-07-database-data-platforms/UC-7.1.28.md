<!-- AUTO-GENERATED from UC-7.1.28.json — DO NOT EDIT -->

---
id: "7.1.28"
title: "PostgreSQL Replication Lag (Streaming)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.28 · PostgreSQL Replication Lag (Streaming)

## Description

`pg_stat_replication` write/flush/replay lag bytes and seconds catch standby drift before read-your-writes violations. Complements generic replication UC with PostgreSQL-native metrics.

## Value

`pg_stat_replication` write/flush/replay lag bytes and seconds catch standby drift before read-your-writes violations. Complements generic replication UC with PostgreSQL-native metrics.

## Implementation

Poll replication view every 1m. Map `application_name` to replica. Alert on replay lag > RPO seconds or LSN gap >100MB. Correlate with `archive_command` and network.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: DB Connect, `pg_stat_replication` scripted export.
• Ensure the following data sources are available: `write_lag`, `flush_lag`, `replay_lag`, `sent_lsn`, `lsn_gap_bytes` (computed in DB Connect SQL via `pg_wal_lsn_diff(sent_lsn, replay_lsn)`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll replication view every 1m. Map `application_name` to replica. Alert on replay lag > RPO seconds or LSN gap >100MB. Correlate with `archive_command` and network.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:pg_replication"
| rex field=replay_lag "(?<replay_lag_sec>\d+)"
| eval replay_lag_sec=tonumber(replay_lag_sec),
       lsn_gap_bytes=tonumber(lsn_gap_bytes)
| where replay_lag_sec > 60 OR lsn_gap_bytes > 104857600
| table application_name client_addr replay_lag_sec lsn_gap_bytes state
```

Understanding this SPL

**PostgreSQL Replication Lag (Streaming)** — `pg_stat_replication` write/flush/replay lag bytes and seconds catch standby drift before read-your-writes violations. Complements generic replication UC with PostgreSQL-native metrics.

Documented **Data sources**: `write_lag`, `flush_lag`, `replay_lag`, `sent_lsn`, `lsn_gap_bytes` (computed in DB Connect SQL via `pg_wal_lsn_diff(sent_lsn, replay_lsn)`). **App/TA** (typical add-on context): DB Connect, `pg_stat_replication` scripted export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:pg_replication. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:pg_replication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **replay_lag_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where replay_lag_sec > 60 OR lsn_gap_bytes > 104857600` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **PostgreSQL Replication Lag (Streaming)**): table application_name client_addr replay_lag_sec lsn_gap_bytes state


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replay lag per standby), Table (standby, lag sec), Single value (max lag).

## SPL

```spl
index=database sourcetype="dbconnect:pg_replication"
| rex field=replay_lag "(?<replay_lag_sec>\d+)"
| eval replay_lag_sec=tonumber(replay_lag_sec),
       lsn_gap_bytes=tonumber(lsn_gap_bytes)
| where replay_lag_sec > 60 OR lsn_gap_bytes > 104857600
| table application_name client_addr replay_lag_sec lsn_gap_bytes state
```

## Visualization

Line chart (replay lag per standby), Table (standby, lag sec), Single value (max lag).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
