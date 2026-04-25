<!-- AUTO-GENERATED from UC-7.5.12.json — DO NOT EDIT -->

---
id: "7.5.12"
title: "Elasticsearch Thread Pool Rejections"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.12 · Elasticsearch Thread Pool Rejections

## Description

Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

## Value

Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

## Implementation

Poll `GET _nodes/stats/thread_pool/search,write,get` every minute. Store cumulative `rejected` counters and compute deltas between samples. Alert when any node shows rejections in a 5-minute window. Correlate with JVM heap and CPU to determine root cause (undersized cluster vs. expensive queries vs. bulk indexing spikes). Do not increase queue sizes as a fix — address the underlying load.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom REST scripted input (`_nodes/stats/thread_pool`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:thread_pool`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _nodes/stats/thread_pool/search,write,get` every minute. Store cumulative `rejected` counters and compute deltas between samples. Alert when any node shows rejections in a 5-minute window. Correlate with JVM heap and CPU to determine root cause (undersized cluster vs. expensive queries vs. bulk indexing spikes). Do not increase queue sizes as a fix — address the underlying load.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:thread_pool"
| eval search_rejected_delta=search.rejected-prev_search_rejected, write_rejected_delta=write.rejected-prev_write_rejected
| where search_rejected_delta > 0 OR write_rejected_delta > 0
| timechart span=5m sum(search_rejected_delta) as search_rejections, sum(write_rejected_delta) as write_rejections by node_name
```

Understanding this SPL

**Elasticsearch Thread Pool Rejections** — Thread pool rejections (HTTP 429) mean the cluster cannot keep up with search or indexing load. Sustained rejections cause data loss on ingest and timeouts on search.

Documented **Data sources**: `sourcetype=elasticsearch:thread_pool`. **App/TA** (typical add-on context): Custom REST scripted input (`_nodes/stats/thread_pool`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:thread_pool. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:thread_pool". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **search_rejected_delta** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where search_rejected_delta > 0 OR write_rejected_delta > 0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by node_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (rejections per pool over time), Bar chart (rejections by node), Single value (total rejections last hour).

## SPL

```spl
index=database sourcetype="elasticsearch:thread_pool"
| eval search_rejected_delta=search.rejected-prev_search_rejected, write_rejected_delta=write.rejected-prev_write_rejected
| where search_rejected_delta > 0 OR write_rejected_delta > 0
| timechart span=5m sum(search_rejected_delta) as search_rejections, sum(write_rejected_delta) as write_rejections by node_name
```

## Visualization

Line chart (rejections per pool over time), Bar chart (rejections by node), Single value (total rejections last hour).

## References

- [Splunk — DB Connect](https://docs.splunk.com/Documentation/DBX/latest/DeployDBX/WhatisDBX)
