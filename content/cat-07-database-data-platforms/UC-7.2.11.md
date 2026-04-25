<!-- AUTO-GENERATED from UC-7.2.11.json — DO NOT EDIT -->

---
id: "7.2.11"
title: "MongoDB Oplog Window"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.11 · MongoDB Oplog Window

## Description

Oplog window shrinking indicates replication at risk of falling behind. Exhausted oplog causes replica set members to resync from scratch (full resync), causing extended downtime.

## Value

Oplog window shrinking indicates replication at risk of falling behind. Exhausted oplog causes replica set members to resync from scratch (full resync), causing extended downtime.

## Implementation

Run scripted input polling `rs.printReplicationInfo()` or `db.getReplicationInfo()` every 15–30 minutes via mongosh. Parse `timeDiff` (oplog window in seconds). Alert when window drops below 24 hours (warning) or 12 hours (critical). Correlate with write throughput and replication lag. Recommend oplog size increase when window consistently shrinks.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: Custom scripted input (mongosh).
• Ensure the following data sources are available: `rs.printReplicationInfo()`, `db.getReplicationInfo()`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run scripted input polling `rs.printReplicationInfo()` or `db.getReplicationInfo()` every 15–30 minutes via mongosh. Parse `timeDiff` (oplog window in seconds). Alert when window drops below 24 hours (warning) or 12 hours (critical). Correlate with write throughput and replication lag. Recommend oplog size increase when window consistently shrinks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:replication_info"
| eval window_hours=round(timeDiff/3600, 1)
| where window_hours < 24
| timechart span=1h latest(window_hours) as oplog_window_hours by host
| where oplog_window_hours < 12
```

Understanding this SPL

**MongoDB Oplog Window** — Oplog window shrinking indicates replication at risk of falling behind. Exhausted oplog causes replica set members to resync from scratch (full resync), causing extended downtime.

Documented **Data sources**: `rs.printReplicationInfo()`, `db.getReplicationInfo()`. **App/TA** (typical add-on context): Custom scripted input (mongosh). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:replication_info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:replication_info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **window_hours** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where window_hours < 24` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where oplog_window_hours < 12` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (oplog window hours over time), Single value (current window hours), Table (hosts with shrinking oplog).

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
index=database sourcetype="mongodb:replication_info"
| eval window_hours=round(timeDiff/3600, 1)
| where window_hours < 24
| timechart span=1h latest(window_hours) as oplog_window_hours by host
| where oplog_window_hours < 12
```

## Visualization

Line chart (oplog window hours over time), Single value (current window hours), Table (hosts with shrinking oplog).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
