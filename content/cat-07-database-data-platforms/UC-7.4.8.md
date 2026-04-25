<!-- AUTO-GENERATED from UC-7.4.8.json — DO NOT EDIT -->

---
id: "7.4.8"
title: "ClickHouse Query Performance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.8 · ClickHouse Query Performance

## Description

Merge operations, insert rate, and query duration indicate system health. Monitoring enables tuning and capacity planning for analytical workloads.

## Value

Merge operations, insert rate, and query duration indicate system health. Monitoring enables tuning and capacity planning for analytical workloads.

## Implementation

Poll `system.query_log` (or enable query_log and ingest via DB Connect/scripted input) for completed queries. Extract query_duration_ms, query_kind, read_rows, memory_usage. Poll `system.metrics` for Merge, Insert, Query metrics. Poll `system.merges` for active merge count and progress. Alert on queries >30s, merge backlog >10, or insert rate drop. Track p95/p99 query duration by type.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: Custom scripted input (ClickHouse system tables).
• Ensure the following data sources are available: `system.query_log`, `system.metrics`, `system.merges`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `system.query_log` (or enable query_log and ingest via DB Connect/scripted input) for completed queries. Extract query_duration_ms, query_kind, read_rows, memory_usage. Poll `system.metrics` for Merge, Insert, Query metrics. Poll `system.merges` for active merge count and progress. Alert on queries >30s, merge backlog >10, or insert rate drop. Track p95/p99 query duration by type.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="clickhouse:query_log"
| where query_duration_ms > 30000
| stats count, avg(query_duration_ms) as avg_duration_ms, sum(read_rows) as total_rows by query_kind, user
| sort -avg_duration_ms
```

Understanding this SPL

**ClickHouse Query Performance** — Merge operations, insert rate, and query duration indicate system health. Monitoring enables tuning and capacity planning for analytical workloads.

Documented **Data sources**: `system.query_log`, `system.metrics`, `system.merges`. **App/TA** (typical add-on context): Custom scripted input (ClickHouse system tables). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: clickhouse:query_log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="clickhouse:query_log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where query_duration_ms > 30000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by query_kind, user** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slow queries with duration and rows), Line chart (query duration p95 over time), Bar chart (merge count and insert rate), Single value (active merges).

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
index=database sourcetype="clickhouse:query_log"
| where query_duration_ms > 30000
| stats count, avg(query_duration_ms) as avg_duration_ms, sum(read_rows) as total_rows by query_kind, user
| sort -avg_duration_ms
```

## Visualization

Table (slow queries with duration and rows), Line chart (query duration p95 over time), Bar chart (merge count and insert rate), Single value (active merges).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
