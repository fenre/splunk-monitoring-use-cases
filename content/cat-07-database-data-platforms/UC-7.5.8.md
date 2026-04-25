<!-- AUTO-GENERATED from UC-7.5.8.json — DO NOT EDIT -->

---
id: "7.5.8"
title: "Elasticsearch Disk Watermark Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.8 · Elasticsearch Disk Watermark Alerts

## Description

Elasticsearch blocks shard allocation when flood-stage watermarks are hit; proactive disk alerts prevent read-only indices and cluster yellow/red states.

## Value

Elasticsearch blocks shard allocation when flood-stage watermarks are hit; proactive disk alerts prevent read-only indices and cluster yellow/red states.

## Implementation

Poll `GET _cat/allocation?bytes=b&h=node,disk.avail,disk.total` or `_nodes/stats/fs` for each data node. Compare `disk.used_percent` to `cluster.routing.allocation.disk.watermark` settings. Alert at low/high/flood thresholds before Elasticsearch enforces blocks. Trigger capacity or ILM actions when trending toward limits.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom scripted input (`_cat/allocation`, node stats fs).
• Ensure the following data sources are available: `sourcetype=elasticsearch:disk_watermark`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _cat/allocation?bytes=b&h=node,disk.avail,disk.total` or `_nodes/stats/fs` for each data node. Compare `disk.used_percent` to `cluster.routing.allocation.disk.watermark` settings. Alert at low/high/flood thresholds before Elasticsearch enforces blocks. Trigger capacity or ILM actions when trending toward limits.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:disk_watermark"
| eval used_pct=round(disk_used_bytes/disk_total_bytes*100,1)
| where used_pct >= watermark_low_pct OR blocks.has_read_only_allow_delete=="true"
| timechart span=5m max(used_pct) as used_pct by node_name
```

Understanding this SPL

**Elasticsearch Disk Watermark Alerts** — Elasticsearch blocks shard allocation when flood-stage watermarks are hit; proactive disk alerts prevent read-only indices and cluster yellow/red states.

Documented **Data sources**: `sourcetype=elasticsearch:disk_watermark`. **App/TA** (typical add-on context): Custom scripted input (`_cat/allocation`, node stats fs). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:disk_watermark. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:disk_watermark". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct >= watermark_low_pct OR blocks.has_read_only_allow_delete=="true"` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (disk % per node), Table (nodes near watermark), Line chart (free space trend).

## SPL

```spl
index=database sourcetype="elasticsearch:disk_watermark"
| eval used_pct=round(disk_used_bytes/disk_total_bytes*100,1)
| where used_pct >= watermark_low_pct OR blocks.has_read_only_allow_delete=="true"
| timechart span=5m max(used_pct) as used_pct by node_name
```

## Visualization

Gauge (disk % per node), Table (nodes near watermark), Line chart (free space trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
