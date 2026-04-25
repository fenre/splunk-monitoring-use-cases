<!-- AUTO-GENERATED from UC-7.5.9.json — DO NOT EDIT -->

---
id: "7.5.9"
title: "Elasticsearch JVM Heap Pressure"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.9 · Elasticsearch JVM Heap Pressure

## Description

High heap usage and frequent GC pause search and indexing and can trigger circuit breakers; JVM trends predict node instability before restarts.

## Value

High heap usage and frequent GC pause search and indexing and can trigger circuit breakers; JVM trends predict node instability before restarts.

## Implementation

Poll JVM stats every 1–2 minutes. Track `heap_used_percent`, young/old GC collection time and count. Alert when heap consistently >85% or old GC time spikes. Correlate with fielddata, merges, and heap dumps policy.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom scripted input (`_nodes/stats/jvm`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:jvm`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll JVM stats every 1–2 minutes. Track `heap_used_percent`, young/old GC collection time and count. Alert when heap consistently >85% or old GC time spikes. Correlate with fielddata, merges, and heap dumps policy.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:jvm"
| eval heap_used_pct=round(mem.heap_used_in_bytes/mem.heap_max_in_bytes*100,1)
| where heap_used_pct > 85 OR gc.collectors.old.collection_time_in_millis > 30000
| timechart span=5m avg(heap_used_pct) as heap_pct, max(gc.collectors.old.collection_time_in_millis) as old_gc_ms by node_name
```

Understanding this SPL

**Elasticsearch JVM Heap Pressure** — High heap usage and frequent GC pause search and indexing and can trigger circuit breakers; JVM trends predict node instability before restarts.

Documented **Data sources**: `sourcetype=elasticsearch:jvm`. **App/TA** (typical add-on context): Custom scripted input (`_nodes/stats/jvm`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:jvm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:jvm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **heap_used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where heap_used_pct > 85 OR gc.collectors.old.collection_time_in_millis > 30000` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (heap % and GC time), Area chart (heap used vs. max), Table (nodes over threshold).

## SPL

```spl
index=database sourcetype="elasticsearch:jvm"
| eval heap_used_pct=round(mem.heap_used_in_bytes/mem.heap_max_in_bytes*100,1)
| where heap_used_pct > 85 OR gc.collectors.old.collection_time_in_millis > 30000
| timechart span=5m avg(heap_used_pct) as heap_pct, max(gc.collectors.old.collection_time_in_millis) as old_gc_ms by node_name
```

## Visualization

Line chart (heap % and GC time), Area chart (heap used vs. max), Table (nodes over threshold).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
