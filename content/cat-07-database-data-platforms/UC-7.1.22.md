<!-- AUTO-GENERATED from UC-7.1.22.json — DO NOT EDIT -->

---
id: "7.1.22"
title: "PostgreSQL WAL Growth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.22 · PostgreSQL WAL Growth

## Description

WAL accumulation indicating replication issues or archival failures. Uncontrolled WAL growth exhausts disk space and can halt the database.

## Value

WAL accumulation indicating replication issues or archival failures. Uncontrolled WAL growth exhausts disk space and can halt the database.

## Implementation

Use DB Connect or a scripted input to poll WAL metrics every 15–30 minutes. Query `pg_current_wal_lsn()` and compare with `pg_walfile_name()` to derive WAL size; alternatively, measure WAL directory on disk. Track replication slot lag via `pg_stat_replication` (replication_lag). Alert when WAL size exceeds threshold (e.g., >10 GB) or when replication lag indicates archival/streaming is falling behind. Correlate with `archive_command` failures and disk space.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Splunk DB Connect or custom scripted input.
• Ensure the following data sources are available: PostgreSQL `pg_stat_replication`, `pg_wal_lsn_diff()`, `pg_ls_waldir()` or filesystem WAL directory size.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use DB Connect or a scripted input to poll WAL metrics every 15–30 minutes. Query `pg_current_wal_lsn()` and compare with `pg_walfile_name()` to derive WAL size; alternatively, measure WAL directory on disk. Track replication slot lag via `pg_stat_replication` (replication_lag). Alert when WAL size exceeds threshold (e.g., >10 GB) or when replication lag indicates archival/streaming is falling behind. Correlate with `archive_command` failures and disk space.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="dbconnect:postgresql_wal"
| eval wal_size_gb=round(wal_size_bytes/1073741824, 2)
| timechart span=1h latest(wal_size_gb) as wal_size_gb by host
| where wal_size_gb > 10
```

Understanding this SPL

**PostgreSQL WAL Growth** — WAL accumulation indicating replication issues or archival failures. Uncontrolled WAL growth exhausts disk space and can halt the database.

Documented **Data sources**: PostgreSQL `pg_stat_replication`, `pg_wal_lsn_diff()`, `pg_ls_waldir()` or filesystem WAL directory size. **App/TA** (typical add-on context): Splunk DB Connect or custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: dbconnect:postgresql_wal. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="dbconnect:postgresql_wal". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **wal_size_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where wal_size_gb > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (WAL size over time), Single value (current WAL size GB), Table (host, WAL size, replication lag).

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
index=database sourcetype="dbconnect:postgresql_wal"
| eval wal_size_gb=round(wal_size_bytes/1073741824, 2)
| timechart span=1h latest(wal_size_gb) as wal_size_gb by host
| where wal_size_gb > 10
```

## Visualization

Line chart (WAL size over time), Single value (current WAL size GB), Table (host, WAL size, replication lag).

## References

- [Splunk DB Connect](https://splunkbase.splunk.com/app/2686)
