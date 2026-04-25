<!-- AUTO-GENERATED from UC-7.3.7.json — DO NOT EDIT -->

---
id: "7.3.7"
title: "Redis Keyspace Hit / Miss Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.7 · Redis Keyspace Hit / Miss Ratio

## Description

Cache effectiveness trending. Low hit ratio indicates cache is not serving requests effectively, increasing load on backing stores.

## Value

Cache effectiveness trending. Low hit ratio indicates cache is not serving requests effectively, increasing load on backing stores.

## Implementation

Poll `redis-cli INFO stats` every 15 minutes. Extract `keyspace_hits` and `keyspace_misses`. Compute hit_ratio = hits/(hits+misses)*100. Alert when hit ratio drops below 90% for sustained periods. Track trend to identify cache warming after restarts or workload shifts. Correlate with eviction rate and memory usage.

## Detailed Implementation

Prerequisites
• In operations we confirm in redis-cli, RedisInsight, or the managed cache console so live stats match Splunk.
• Install and configure the required add-on or app: Custom scripted input (redis-cli INFO stats).
• Ensure the following data sources are available: redis-cli INFO stats (keyspace_hits, keyspace_misses).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `redis-cli INFO stats` every 15 minutes. Extract `keyspace_hits` and `keyspace_misses`. Compute hit_ratio = hits/(hits+misses)*100. Alert when hit ratio drops below 90% for sustained periods. Track trend to identify cache warming after restarts or workload shifts. Correlate with eviction rate and memory usage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="redis:info"
| eval total_ops=keyspace_hits+keyspace_misses
| eval hit_ratio_pct=round(100*keyspace_hits/nullif(total_ops,0), 2)
| where hit_ratio_pct < 90
| timechart span=15m avg(hit_ratio_pct) as hit_ratio_pct by host
```

Understanding this SPL

**Redis Keyspace Hit / Miss Ratio** — Cache effectiveness trending. Low hit ratio indicates cache is not serving requests effectively, increasing load on backing stores.

Documented **Data sources**: redis-cli INFO stats (keyspace_hits, keyspace_misses). **App/TA** (typical add-on context): Custom scripted input (redis-cli INFO stats). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: redis:info. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="redis:info". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **total_ops** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **hit_ratio_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio_pct < 90` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (keyspace hit ratio %), Line chart (hit ratio over time), Table (hosts with low hit ratio).

## SPL

```spl
index=database sourcetype="redis:info"
| eval total_ops=keyspace_hits+keyspace_misses
| eval hit_ratio_pct=round(100*keyspace_hits/nullif(total_ops,0), 2)
| where hit_ratio_pct < 90
| timechart span=15m avg(hit_ratio_pct) as hit_ratio_pct by host
```

## Visualization

Gauge (keyspace hit ratio %), Line chart (hit ratio over time), Table (hosts with low hit ratio).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
