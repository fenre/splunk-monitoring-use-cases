<!-- AUTO-GENERATED from UC-7.2.7.json — DO NOT EDIT -->

---
id: "7.2.7"
title: "Connection Count Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.7 · Connection Count Monitoring

## Description

Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment or connection pooling.

## Value

Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment or connection pooling.

## Implementation

Poll connection metrics every 5 minutes. Calculate percentage of max connections used. Alert at 80% and 95%. Track by client application to identify connection leaks.

## Detailed Implementation

Prerequisites
• In operations we confirm in redis-cli, RedisInsight, or the managed cache console so live stats match Splunk.
• Install and configure the required add-on or app: Custom scripted input.
• Ensure the following data sources are available: MongoDB `serverStatus().connections`, Redis `INFO clients`, Elasticsearch `_nodes/stats/transport`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll connection metrics every 5 minutes. Calculate percentage of max connections used. Alert at 80% and 95%. Track by client application to identify connection leaks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:server_status"
| eval pct_used=round(connections.current/connections.available*100,1)
| timechart span=5m max(pct_used) as connection_pct by host
| where connection_pct > 80
```

Understanding this SPL

**Connection Count Monitoring** — Approaching connection limits causes client rejections. Monitoring enables proactive limit adjustment or connection pooling.

Documented **Data sources**: MongoDB `serverStatus().connections`, Redis `INFO clients`, Elasticsearch `_nodes/stats/transport`. **App/TA** (typical add-on context): Custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:server_status. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:server_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **pct_used** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where connection_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (% connections used per node), Line chart (connection count over time), Table (nodes approaching limit).

## SPL

```spl
index=database sourcetype="mongodb:server_status"
| eval pct_used=round(connections.current/connections.available*100,1)
| timechart span=5m max(pct_used) as connection_pct by host
| where connection_pct > 80
```

## Visualization

Gauge (% connections used per node), Line chart (connection count over time), Table (nodes approaching limit).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
