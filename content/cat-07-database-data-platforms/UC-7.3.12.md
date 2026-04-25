<!-- AUTO-GENERATED from UC-7.3.12.json — DO NOT EDIT -->

---
id: "7.3.12"
title: "Azure SQL Database DTU Exhaustion"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.12 · Azure SQL Database DTU Exhaustion

## Description

DTU/vCore saturation causes throttling and query timeouts. Distinct from generic RDS CPU for Azure-only deployments.

## Value

DTU/vCore saturation causes throttling and query timeouts. Distinct from generic RDS CPU for Azure-only deployments.

## Implementation

Enable Azure Monitor metrics for SQL DB/elastic pool. Alert on sustained high DTU%. Recommend tier upgrade or elastic pool rebalance.

## Detailed Implementation

Prerequisites
• In operations we align Splunk with the cloud provider’s database console and metrics to rule out a platform maintenance window.
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `dtu_consumption_percent`, `cpu_percent`, `data_io_percent`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Azure Monitor metrics for SQL DB/elastic pool. Alert on sustained high DTU%. Recommend tier upgrade or elastic pool rebalance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:sql:metrics"
| where dtu_consumption_percent > 85 OR cpu_percent > 90
| timechart span=5m max(dtu_consumption_percent) as dtu_pct by database_name, elastic_pool_name
```

Understanding this SPL

**Azure SQL Database DTU Exhaustion** — DTU/vCore saturation causes throttling and query timeouts. Distinct from generic RDS CPU for Azure-only deployments.

Documented **Data sources**: `dtu_consumption_percent`, `cpu_percent`, `data_io_percent`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:sql:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:sql:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where dtu_consumption_percent > 85 OR cpu_percent > 90` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by database_name, elastic_pool_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (DTU %), Gauge (current DTU), Table (databases over 85%).

## SPL

```spl
index=azure sourcetype="azure:sql:metrics"
| where dtu_consumption_percent > 85 OR cpu_percent > 90
| timechart span=5m max(dtu_consumption_percent) as dtu_pct by database_name, elastic_pool_name
```

## Visualization

Line chart (DTU %), Gauge (current DTU), Table (databases over 85%).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
