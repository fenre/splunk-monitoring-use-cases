<!-- AUTO-GENERATED from UC-7.3.15.json — DO NOT EDIT -->

---
id: "7.3.15"
title: "Read Replica Lag Trending (Percentiles)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.15 · Read Replica Lag Trending (Percentiles)

## Description

p95/p99 replica lag exposes tail behavior missed by max-only dashboards. Applies to RDS, Aurora, and Azure read replicas.

## Value

p95/p99 replica lag exposes tail behavior missed by max-only dashboards. Applies to RDS, Aurora, and Azure read replicas.

## Implementation

Set SLA based on app freshness needs. Alert on p95 > threshold for 15m. Compare primary write IOPS to replica apply lag.

## Detailed Implementation

Prerequisites
• In operations we confirm in MySQL Workbench, Percona tools, or the managed MySQL console.
• Install and configure the required add-on or app: CloudWatch, Azure Monitor.
• Ensure the following data sources are available: `ReplicaLag` (seconds), `physical_replication_delay`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Set SLA based on app freshness needs. Alert on p95 > threshold for 15m. Compare primary write IOPS to replica apply lag.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m perc95(Maximum) as p95_lag, max(Maximum) as max_lag by DBInstanceIdentifier
| where p95_lag > 30
```

Understanding this SPL

**Read Replica Lag Trending (Percentiles)** — p95/p99 replica lag exposes tail behavior missed by max-only dashboards. Applies to RDS, Aurora, and Azure read replicas.

Documented **Data sources**: `ReplicaLag` (seconds), `physical_replication_delay`. **App/TA** (typical add-on context): CloudWatch, Azure Monitor. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by DBInstanceIdentifier** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p95_lag > 30` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p95/p99 replica lag), Table (replicas breaching SLA), Single value (worst p95).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ReplicaLag"
| timechart span=5m perc95(Maximum) as p95_lag, max(Maximum) as max_lag by DBInstanceIdentifier
| where p95_lag > 30
```

## Visualization

Line chart (p95/p99 replica lag), Table (replicas breaching SLA), Single value (worst p95).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
