<!-- AUTO-GENERATED from UC-7.3.8.json — DO NOT EDIT -->

---
id: "7.3.8"
title: "Aurora Serverless Scaling Events"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.3.8 · Aurora Serverless Scaling Events

## Description

ACU (capacity unit) scale-up/down events explain latency and cost. Tracks whether scaling policy matches workload bursts.

## Value

ACU (capacity unit) scale-up/down events explain latency and cost. Tracks whether scaling policy matches workload bursts.

## Implementation

Ingest ACU metric and RDS events for scale actions. Alert on repeated scale-to-max or throttling. Correlate with `DatabaseConnections` and CPU.

## Detailed Implementation

Prerequisites
• In operations we align Splunk with the cloud provider’s database console and metrics to rule out a platform maintenance window.
• Install and configure the required add-on or app: `Splunk_TA_aws` (RDS events, CloudWatch).
• Ensure the following data sources are available: RDS event categories `notification`, `serverless`, CloudWatch `ServerlessDatabaseCapacity`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest ACU metric and RDS events for scale actions. Alert on repeated scale-to-max or throttling. Correlate with `DatabaseConnections` and CPU.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ServerlessDatabaseCapacity"
| timechart span=5m avg(Average) as acu by DBClusterIdentifier
```

Understanding this SPL

**Aurora Serverless Scaling Events** — ACU (capacity unit) scale-up/down events explain latency and cost. Tracks whether scaling policy matches workload bursts.

Documented **Data sources**: RDS event categories `notification`, `serverless`, CloudWatch `ServerlessDatabaseCapacity`. **App/TA** (typical add-on context): `Splunk_TA_aws` (RDS events, CloudWatch). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by DBClusterIdentifier** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (ACU over time), Timeline (scaling events), Table (clusters at max ACU).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/RDS" metric_name="ServerlessDatabaseCapacity"
| timechart span=5m avg(Average) as acu by DBClusterIdentifier
```

## Visualization

Line chart (ACU over time), Timeline (scaling events), Table (clusters at max ACU).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
