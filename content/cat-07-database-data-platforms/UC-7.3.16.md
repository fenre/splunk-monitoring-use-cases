<!-- AUTO-GENERATED from UC-7.3.16.json — DO NOT EDIT -->

---
id: "7.3.16"
title: "Azure SQL Managed Instance Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.16 · Azure SQL Managed Instance Resource Utilization

## Description

SQL Managed Instance provides near-100% SQL Server compatibility in Azure. CPU, storage I/O, and memory pressure against provisioned limits directly impact query performance and can cause throttling.

## Value

SQL Managed Instance provides near-100% SQL Server compatibility in Azure. CPU, storage I/O, and memory pressure against provisioned limits directly impact query performance and can cause throttling.

## Implementation

Collect Azure Monitor metrics for SQL Managed Instance. Key metrics: `avg_cpu_percent` (alert >85% sustained), `io_bytes_read`/`io_bytes_written` against provisioned IOPS for the service tier, and `storage_space_used_mb` versus reserved storage. Monitor `virtual_core_count` utilization to guide tier scaling decisions. Alert on sustained high CPU and storage approaching the limit.

## Detailed Implementation

Prerequisites
• In operations we align Splunk with the cloud provider’s database console and metrics to rule out a platform maintenance window.
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics).
• Ensure the following data sources are available: `sourcetype=azure:monitor:metric` (Microsoft.Sql/managedInstances).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Azure Monitor metrics for SQL Managed Instance. Key metrics: `avg_cpu_percent` (alert >85% sustained), `io_bytes_read`/`io_bytes_written` against provisioned IOPS for the service tier, and `storage_space_used_mb` versus reserved storage. Monitor `virtual_core_count` utilization to guide tier scaling decisions. Alert on sustained high CPU and storage approaching the limit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.sql/managedinstances"
| where metric_name IN ("avg_cpu_percent","io_bytes_read","io_bytes_written","storage_space_used_mb")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

Understanding this SPL

**Azure SQL Managed Instance Resource Utilization** — SQL Managed Instance provides near-100% SQL Server compatibility in Azure. CPU, storage I/O, and memory pressure against provisioned limits directly impact query performance and can cause throttling.

Documented **Data sources**: `sourcetype=azure:monitor:metric` (Microsoft.Sql/managedInstances). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:metric. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:metric". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where metric_name IN ("avg_cpu_percent","io_bytes_read","io_bytes_written","storage_space_used_mb")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by metric_name, resource_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (CPU % over time), Gauge (storage used vs. limit), Table (instances near capacity).

## SPL

```spl
index=cloud sourcetype="azure:monitor:metric" resource_type="microsoft.sql/managedinstances"
| where metric_name IN ("avg_cpu_percent","io_bytes_read","io_bytes_written","storage_space_used_mb")
| timechart span=5m avg(average) as value by metric_name, resource_name
```

## Visualization

Line chart (CPU % over time), Gauge (storage used vs. limit), Table (instances near capacity).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
