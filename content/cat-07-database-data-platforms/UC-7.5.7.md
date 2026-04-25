<!-- AUTO-GENERATED from UC-7.5.7.json — DO NOT EDIT -->

---
id: "7.5.7"
title: "Solr Replication Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.7 · Solr Replication Lag

## Description

Followers lagging behind leaders serve stale results and extend recovery time; catching replication gaps protects read consistency and failover readiness.

## Value

Followers lagging behind leaders serve stale results and extend recovery time; catching replication gaps protects read consistency and failover readiness.

## Implementation

Ingest Solr Cloud replica state (version, generation, replication timing) from admin API or `REPLICATION` metrics. For standalone Solr, use master/slave `fetch` lag fields. Alert when replica index version lags leader beyond SLA (bytes or generations). Investigate network, disk, and TLog backlog.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (Solr Cloud `CLUSTERSTATUS`, replica stats).
• Ensure the following data sources are available: `sourcetype=solr:replication`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest Solr Cloud replica state (version, generation, replication timing) from admin API or `REPLICATION` metrics. For standalone Solr, use master/slave `fetch` lag fields. Alert when replica index version lags leader beyond SLA (bytes or generations). Investigate network, disk, and TLog backlog.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="solr:replication"
| eval lag_bytes=leader_version - replica_version
| where lag_bytes > 1048576 OR index_version_lag > 100
| stats max(lag_bytes) as max_lag, max(replication_time_ms) as max_rep_ms by collection, shard, replica
| sort -max_lag
```

Understanding this SPL

**Solr Replication Lag** — Followers lagging behind leaders serve stale results and extend recovery time; catching replication gaps protects read consistency and failover readiness.

Documented **Data sources**: `sourcetype=solr:replication`. **App/TA** (typical add-on context): Custom scripted input (Solr Cloud `CLUSTERSTATUS`, replica stats). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: solr:replication. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="solr:replication". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **lag_bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where lag_bytes > 1048576 OR index_version_lag > 100` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by collection, shard, replica** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replication lag over time), Table (replicas over SLA), Single value (max lag per collection).

## SPL

```spl
index=database sourcetype="solr:replication"
| eval lag_bytes=leader_version - replica_version
| where lag_bytes > 1048576 OR index_version_lag > 100
| stats max(lag_bytes) as max_lag, max(replication_time_ms) as max_rep_ms by collection, shard, replica
| sort -max_lag
```

## Visualization

Line chart (replication lag over time), Table (replicas over SLA), Single value (max lag per collection).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
