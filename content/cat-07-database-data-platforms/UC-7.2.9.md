<!-- AUTO-GENERATED from UC-7.2.9.json — DO NOT EDIT -->

---
id: "7.2.9"
title: "Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.9 · Memory Utilization

## Description

NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

## Value

NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

## Implementation

Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.

## Detailed Implementation

Prerequisites
• In operations we confirm in redis-cli, RedisInsight, or the managed cache console so live stats match Splunk.
• Install and configure the required add-on or app: Custom scripted input, JMX.
• Ensure the following data sources are available: Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll memory metrics every 5 minutes. Track used vs max memory, eviction rate, and cache hit ratio. Alert when memory exceeds 85% or eviction rate spikes. Recommend sizing adjustments based on trends.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```

Understanding this SPL

**Memory Utilization** — NoSQL databases are memory-intensive. Evictions indicate undersized cache, causing disk reads and performance degradation.

Documented **Data sources**: Redis `INFO memory`, MongoDB WiredTiger cache stats, Cassandra JMX heap metrics. **App/TA** (typical add-on context): Custom scripted input, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **mem_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where memory_pct > 85` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).

## SPL

```spl
index=database sourcetype="redis:info"
| eval mem_pct=round(used_memory/maxmemory*100,1)
| timechart span=5m max(mem_pct) as memory_pct, sum(evicted_keys) as evictions by host
| where memory_pct > 85
```

## Visualization

Gauge (memory % per node), Line chart (memory + evictions), Table (nodes with high utilization).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
