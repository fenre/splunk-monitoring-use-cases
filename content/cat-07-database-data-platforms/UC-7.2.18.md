<!-- AUTO-GENERATED from UC-7.2.18.json — DO NOT EDIT -->

---
id: "7.2.18"
title: "MongoDB Oplog Window Sufficiency"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.18 · MongoDB Oplog Window Sufficiency

## Description

Validates minimum oplog window hours against replica catch-up time under peak load. Extends oplog monitoring with capacity-style thresholds per deployment class.

## Value

Validates minimum oplog window hours against replica catch-up time under peak load. Extends oplog monitoring with capacity-style thresholds per deployment class.

## Implementation

Define minimum window per environment in lookup. Alert below tier minimum. Recommend oplog size change when consistently borderline.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: mongosh scripted input.
• Ensure the following data sources are available: `getReplicationInfo()`, `rs.printReplicationInfo()`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define minimum window per environment in lookup. Alert below tier minimum. Recommend oplog size change when consistently borderline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:replication_info"
| eval window_hrs=round(timeDiff/3600,2)
| lookup mongo_replica_tier class OUTPUT min_oplog_window_hrs
| where window_hrs < min_oplog_window_hrs
| table host window_hrs min_oplog_window_hrs
```

Understanding this SPL

**MongoDB Oplog Window Sufficiency** — Validates minimum oplog window hours against replica catch-up time under peak load. Extends oplog monitoring with capacity-style thresholds per deployment class.

Documented **Data sources**: `getReplicationInfo()`, `rs.printReplicationInfo()`. **App/TA** (typical add-on context): mongosh scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:replication_info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:replication_info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **window_hrs** — often to normalize units, derive a ratio, or prepare for thresholds.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where window_hrs < min_oplog_window_hrs` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MongoDB Oplog Window Sufficiency**): table host window_hrs min_oplog_window_hrs


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (oplog window hours), Table (hosts below tier min), Gauge (worst window).

## SPL

```spl
index=database sourcetype="mongodb:replication_info"
| eval window_hrs=round(timeDiff/3600,2)
| lookup mongo_replica_tier class OUTPUT min_oplog_window_hrs
| where window_hrs < min_oplog_window_hrs
| table host window_hrs min_oplog_window_hrs
```

## Visualization

Line chart (oplog window hours), Table (hosts below tier min), Gauge (worst window).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
