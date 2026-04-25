<!-- AUTO-GENERATED from UC-7.2.4.json — DO NOT EDIT -->

---
id: "7.2.4"
title: "Shard Imbalance Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.4 · Shard Imbalance Detection

## Description

Uneven shard distribution causes hot spots and performance inconsistency. Rebalancing prevents overloaded nodes.

## Value

Uneven shard distribution causes hot spots and performance inconsistency. Rebalancing prevents overloaded nodes.

## Implementation

Poll shard statistics periodically. Calculate per-shard deviation from average. Alert when any shard deviates >20% from mean size. For Elasticsearch, track unassigned shards as a separate critical alert.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: MongoDB `sh.status()`, Elasticsearch `_cat/shards`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll shard statistics periodically. Calculate per-shard deviation from average. Alert when any shard deviates >20% from mean size. For Elasticsearch, track unassigned shards as a separate critical alert.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:shard_status"
| stats sum(count) as doc_count, sum(size) as data_size by shard
| eventstats avg(doc_count) as avg_count
| eval imbalance_pct=round(abs(doc_count-avg_count)/avg_count*100,1)
| where imbalance_pct > 20
```

Understanding this SPL

**Shard Imbalance Detection** — Uneven shard distribution causes hot spots and performance inconsistency. Rebalancing prevents overloaded nodes.

Documented **Data sources**: MongoDB `sh.status()`, Elasticsearch `_cat/shards`. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:shard_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:shard_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by shard** so each row reflects one combination of those dimensions.
• `eventstats` aggregates the pipeline (counts, distinct values, sums, percentiles, etc.) into fewer rows.
• `eval` defines or adjusts **imbalance_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where imbalance_pct > 20` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (data size per shard), Table (shards with imbalance), Single value (max imbalance %).

## SPL

```spl
index=database sourcetype="mongodb:shard_status"
| stats sum(count) as doc_count, sum(size) as data_size by shard
| eventstats avg(doc_count) as avg_count
| eval imbalance_pct=round(abs(doc_count-avg_count)/avg_count*100,1)
| where imbalance_pct > 20
```

## Visualization

Bar chart (data size per shard), Table (shards with imbalance), Single value (max imbalance %).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
