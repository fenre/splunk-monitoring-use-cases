<!-- AUTO-GENERATED from UC-7.4.15.json — DO NOT EDIT -->

---
id: "7.4.15"
title: "Azure Synapse Analytics SQL Pool Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.4.15 · Azure Synapse Analytics SQL Pool Performance

## Description

Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

## Value

Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

## Implementation

Collect Azure Monitor metrics for Synapse SQL pools. Alert when `DWUUsedPercent` exceeds 90% sustained (scale up DWU), when `QueuedQueries` exceeds 10 (resource contention), or when `AdaptiveCacheHitPercent` drops below 50% (cold cache after pause/resume). Enable diagnostics for `SqlRequests` to track query execution times and identify long-running queries consuming resources.

## Detailed Implementation

Prerequisites
• In operations we cross-check backup reality in the right console for each engine: `msdb` and SSMS for SQL Server, RMAN and Enterprise Manager (or DBA views) for Oracle, and the postgres or managed-service view for PostgreSQL, alongside Splunk.
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for Synapse SQL pools. Alert when `DWUUsedPercent` exceeds 90% sustained (scale up DWU), when `QueuedQueries` exceeds 10 (resource contention), or when `AdaptiveCacheHitPercent` drops below 50% (cold cache after pause/resume). Enable diagnostics for `SqlRequests` to track query execution times and identify long-running queries consuming resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.synapse/workspaces/sqlpools"
| where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

Understanding this SPL

**Azure Synapse Analytics SQL Pool Performance** — Synapse dedicated SQL pools have DWU-based resource limits. Queries competing for resources cause queueing, and tempdb contention degrades batch processing. Monitoring ensures analytics workloads meet SLAs.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Synapse/workspaces/sqlPools), `sourcetype=azure:diagnostics` (SqlRequests). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, resource_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DWU % and queued queries), Table (long-running queries), Gauge (cache hit ratio).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.synapse/workspaces/sqlpools"
| where metric_name IN ("DWUUsedPercent","ActiveQueries","QueuedQueries","AdaptiveCacheHitPercent")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

## Visualization

Line chart (DWU % and queued queries), Table (long-running queries), Gauge (cache hit ratio).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
