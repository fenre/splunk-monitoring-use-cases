<!-- AUTO-GENERATED from UC-7.4.11.json — DO NOT EDIT -->

---
id: "7.4.11"
title: "Redshift Query Queue Depth"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.11 · Redshift Query Queue Depth

## Description

WLM queue length and max execution time show concurrency saturation. Growing queue depth precedes disk-based spills and timeouts.

## Value

WLM queue length and max execution time show concurrency saturation. Growing queue depth precedes disk-based spills and timeouts.

## Implementation

Map queue names to workload classes. Alert when queue_depth sustained above SLA. Tune WLM slots or concurrency scaling.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: CloudWatch, `STL_WLM_QUERY` export.
• Ensure the following data sources are available: `WLMQueueDepth`, `WLMQueriesCompletedPerSecond`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map queue names to workload classes. Alert when queue_depth sustained above SLA. Tune WLM slots or concurrency scaling.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="WLMQueueDepth"
| timechart span=5m max(Maximum) as queue_depth by ClusterIdentifier, QueueName
| where queue_depth > 10
```

Understanding this SPL

**Redshift Query Queue Depth** — WLM queue length and max execution time show concurrency saturation. Growing queue depth precedes disk-based spills and timeouts.

Documented **Data sources**: `WLMQueueDepth`, `WLMQueriesCompletedPerSecond`. **App/TA** (typical add-on context): CloudWatch, `STL_WLM_QUERY` export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by ClusterIdentifier, QueueName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where queue_depth > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue depth), Table (cluster, queue, depth), Single value (max depth).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/Redshift" metric_name="WLMQueueDepth"
| timechart span=5m max(Maximum) as queue_depth by ClusterIdentifier, QueueName
| where queue_depth > 10
```

## Visualization

Line chart (queue depth), Table (cluster, queue, depth), Single value (max depth).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
