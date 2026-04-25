<!-- AUTO-GENERATED from UC-7.3.17.json — DO NOT EDIT -->

---
id: "7.3.17"
title: "Azure SQL Managed Instance Failover Group Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.3.17 · Azure SQL Managed Instance Failover Group Status

## Description

Failover groups provide geo-redundancy for SQL Managed Instance. Monitoring replication lag and failover events ensures disaster recovery readiness and detects unplanned failovers.

## Value

Failover groups provide geo-redundancy for SQL Managed Instance. Monitoring replication lag and failover events ensures disaster recovery readiness and detects unplanned failovers.

## Implementation

Collect Activity Log events for failover group operations and Azure Monitor metrics for replication state. Alert on unplanned failover events (not initiated by known maintenance windows). Monitor `ReplicationState` metric — alert when state is not `SEEDING` or `CATCH_UP` for extended periods. Track replication lag to validate RPO compliance.

## Detailed Implementation

Prerequisites
• In operations we align Splunk with the cloud provider’s database console and metrics to rule out a platform maintenance window.
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/Activity Log).
• Ensure the following data sources are available: `sourcetype=azure:monitor:activity`, `sourcetype=azure:monitor:metric`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Activity Log events for failover group operations and Azure Monitor metrics for replication state. Alert on unplanned failover events (not initiated by known maintenance windows). Monitor `ReplicationState` metric — alert when state is not `SEEDING` or `CATCH_UP` for extended periods. Track replication lag to validate RPO compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:monitor:activity" resourceType="microsoft.sql/managedinstances/failovergroups"
| where operationName="Microsoft.Sql/managedInstances/failoverGroups/failover/action"
| table _time, caller, status, resource_name
| sort -_time
```

Understanding this SPL

**Azure SQL Managed Instance Failover Group Status** — Failover groups provide geo-redundancy for SQL Managed Instance. Monitoring replication lag and failover events ensures disaster recovery readiness and detects unplanned failovers.

Documented **Data sources**: `sourcetype=azure:monitor:activity`, `sourcetype=azure:monitor:metric`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor metrics/Activity Log). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:monitor:activity, microsoft.sql/managedinstances/failovergroups. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:monitor:activity". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where operationName="Microsoft.Sql/managedInstances/failoverGroups/failover/action"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Azure SQL Managed Instance Failover Group Status**): table _time, caller, status, resource_name
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (failover events), Single value (current replication state), Table (failover history).

## SPL

```spl
index=cloud sourcetype="azure:monitor:activity" resourceType="microsoft.sql/managedinstances/failovergroups"
| where operationName="Microsoft.Sql/managedInstances/failoverGroups/failover/action"
| table _time, caller, status, resource_name
| sort -_time
```

## Visualization

Timeline (failover events), Single value (current replication state), Table (failover history).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
