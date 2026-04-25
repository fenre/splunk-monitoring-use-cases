<!-- AUTO-GENERATED from UC-7.2.6.json — DO NOT EDIT -->

---
id: "7.2.6"
title: "GC Pause Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.6 · GC Pause Detection

## Description

Long GC pauses in Java-based databases (Cassandra, Elasticsearch) cause request timeouts and can trigger node eviction from the cluster.

## Value

Long GC pauses in Java-based databases (Cassandra, Elasticsearch) cause request timeouts and can trigger node eviction from the cluster.

## Implementation

Configure JVM GC logging on all Java-based database nodes. Forward GC logs to Splunk with proper field extraction. Alert on pauses >500ms. Track GC frequency and total pause time per hour. Recommend heap tuning when pauses are chronic.

## Detailed Implementation

Prerequisites
• In operations we confirm with nodetool, the CQL layer, and cluster logs so ring and replica state match what Splunk shows.
• Install and configure the required add-on or app: GC log parsing, JMX.
• Ensure the following data sources are available: JVM GC logs (`gc.log`), JMX GC metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure JVM GC logging on all Java-based database nodes. Forward GC logs to Splunk with proper field extraction. Alert on pauses >500ms. Track GC frequency and total pause time per hour. Recommend heap tuning when pauses are chronic.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="jvm:gc"
| where gc_pause_ms > 500
| stats count, avg(gc_pause_ms) as avg_pause, max(gc_pause_ms) as max_pause by host, gc_type
| where max_pause > 1000
```

Understanding this SPL

**GC Pause Detection** — Long GC pauses in Java-based databases (Cassandra, Elasticsearch) cause request timeouts and can trigger node eviction from the cluster.

Documented **Data sources**: JVM GC logs (`gc.log`), JMX GC metrics. **App/TA** (typical add-on context): GC log parsing, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: jvm:gc. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="jvm:gc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where gc_pause_ms > 500` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, gc_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where max_pause > 1000` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (GC pause duration over time), Histogram (pause distribution), Table (hosts with excessive GC).

## SPL

```spl
index=database sourcetype="jvm:gc"
| where gc_pause_ms > 500
| stats count, avg(gc_pause_ms) as avg_pause, max(gc_pause_ms) as max_pause by host, gc_type
| where max_pause > 1000
```

## Visualization

Line chart (GC pause duration over time), Histogram (pause distribution), Table (hosts with excessive GC).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
