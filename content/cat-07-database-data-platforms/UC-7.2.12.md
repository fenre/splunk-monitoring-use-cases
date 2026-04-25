<!-- AUTO-GENERATED from UC-7.2.12.json — DO NOT EDIT -->

---
id: "7.2.12"
title: "MongoDB WiredTiger Cache Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.12 · MongoDB WiredTiger Cache Pressure

## Description

Cache dirty/used ratio approaching eviction thresholds causes increased disk I/O and degraded query performance. Early detection enables cache sizing or workload tuning.

## Value

Cache dirty/used ratio approaching eviction thresholds causes increased disk I/O and degraded query performance. Early detection enables cache sizing or workload tuning.

## Implementation

Poll `db.serverStatus()` via mongosh every 5 minutes. Extract `wiredTiger.cache`; map MongoDB fields ("bytes dirty in the cache", "bytes currently in the cache", "maximum bytes configured") to bytes_dirty, bytes_currently_in_the_cache, cache_maximum_bytes_configured in the scripted input output. Compute dirty and used percentages. Alert when dirty_pct >20% (eviction pressure) or used_pct >90%. Track eviction count and evicted pages. Correlate with workload spikes.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: Custom scripted input (mongosh serverStatus).
• Ensure the following data sources are available: `db.serverStatus().wiredTiger.cache`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `db.serverStatus()` via mongosh every 5 minutes. Extract `wiredTiger.cache`; map MongoDB fields ("bytes dirty in the cache", "bytes currently in the cache", "maximum bytes configured") to bytes_dirty, bytes_currently_in_the_cache, cache_maximum_bytes_configured in the scripted input output. Compute dirty and used percentages. Alert when dirty_pct >20% (eviction pressure) or used_pct >90%. Track eviction count and evicted pages. Correlate with workload spikes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:server_status"
| eval dirty_pct=round(bytes_dirty/bytes_currently_in_the_cache*100, 1)
| eval used_pct=round(bytes_currently_in_the_cache/cache_maximum_bytes_configured*100, 1)
| where dirty_pct > 20 OR used_pct > 90
| timechart span=5m avg(dirty_pct) as dirty_pct, avg(used_pct) as used_pct by host
```

Understanding this SPL

**MongoDB WiredTiger Cache Pressure** — Cache dirty/used ratio approaching eviction thresholds causes increased disk I/O and degraded query performance. Early detection enables cache sizing or workload tuning.

Documented **Data sources**: `db.serverStatus().wiredTiger.cache`. **App/TA** (typical add-on context): Custom scripted input (mongosh serverStatus). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:server_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:server_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **dirty_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dirty_pct > 20 OR used_pct > 90` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (dirty % and used % over time), Gauge (cache pressure), Table (hosts with high cache pressure).

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
index=database sourcetype="mongodb:server_status"
| eval dirty_pct=round(bytes_dirty/bytes_currently_in_the_cache*100, 1)
| eval used_pct=round(bytes_currently_in_the_cache/cache_maximum_bytes_configured*100, 1)
| where dirty_pct > 20 OR used_pct > 90
| timechart span=5m avg(dirty_pct) as dirty_pct, avg(used_pct) as used_pct by host
```

## Visualization

Line chart (dirty % and used % over time), Gauge (cache pressure), Table (hosts with high cache pressure).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
