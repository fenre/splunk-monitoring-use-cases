<!-- AUTO-GENERATED from UC-7.3.3.json — DO NOT EDIT -->

---
id: "7.3.3"
title: "Read Replica Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.3 · Read Replica Lag

## Description

Replica lag affects read consistency for applications using read replicas. Monitoring prevents stale data serving.

## Value

Replica lag affects read consistency for applications using read replicas. Monitoring prevents stale data serving.

## Implementation

Ingest CloudWatch RDS metrics. Alert when ReplicaLag exceeds application tolerance (e.g., >30 seconds). Track trend and correlate with write workload spikes. Alert on replica lag growing consistently.

## Detailed Implementation

Prerequisites
• In operations we confirm in MySQL Workbench, Percona tools, or the managed MySQL console.
• Install and configure the required add-on or app: Cloud provider TAs (CloudWatch, Azure Monitor).
• Ensure the following data sources are available: CloudWatch `ReplicaLag` metric, Azure SQL `replication_lag`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest CloudWatch RDS metrics. Alert when ReplicaLag exceeds application tolerance (e.g., >30 seconds). Track trend and correlate with write workload spikes. Alert on replica lag growing consistently.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m max(Maximum) as replica_lag_sec by DBInstanceIdentifier
| where replica_lag_sec > 30
```

Understanding this SPL

**Read Replica Lag** — Replica lag affects read consistency for applications using read replicas. Monitoring prevents stale data serving.

Documented **Data sources**: CloudWatch `ReplicaLag` metric, Azure SQL `replication_lag`. **App/TA** (typical add-on context): Cloud provider TAs (CloudWatch, Azure Monitor). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by DBInstanceIdentifier** — ideal for trending and alerting on this use case.
• Filters the current rows with `where replica_lag_sec > 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (replica lag over time), Single value (current max lag), Table (replicas with lag).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m max(Maximum) as replica_lag_sec by DBInstanceIdentifier
| where replica_lag_sec > 30
```

## Visualization

Line chart (replica lag over time), Single value (current max lag), Table (replicas with lag).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
