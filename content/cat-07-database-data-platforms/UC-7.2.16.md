<!-- AUTO-GENERATED from UC-7.2.16.json — DO NOT EDIT -->

---
id: "7.2.16"
title: "DynamoDB Throttling Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.2.16 · DynamoDB Throttling Events

## Description

Read/write throttle events mean application retries and latency spikes. Identifies hot partitions and undersized capacity modes.

## Value

Read/write throttle events mean application retries and latency spikes. Identifies hot partitions and undersized capacity modes.

## Implementation

Enable DynamoDB metrics with table dimension. Alert on any sustained throttling. Correlate with hot key patterns from access logs if available.

## Detailed Implementation

Prerequisites
• In operations we confirm in the vendor database console and native system views for the engine this search targets so live metrics match what Splunk shows.
• Install and configure the required add-on or app: `Splunk_TA_aws` (CloudWatch).
• Ensure the following data sources are available: `UserErrors`, `ThrottledRequests`, `ConsumedReadCapacityUnits`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DynamoDB metrics with table dimension. Alert on any sustained throttling. Correlate with hot key patterns from access logs if available.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| timechart span=5m sum(Sum) as throttled by TableName, Operation
| where throttled > 0
```

Understanding this SPL

**DynamoDB Throttling Events** — Read/write throttle events mean application retries and latency spikes. Identifies hot partitions and undersized capacity modes.

Documented **Data sources**: `UserErrors`, `ThrottledRequests`, `ConsumedReadCapacityUnits`. **App/TA** (typical add-on context): `Splunk_TA_aws` (CloudWatch). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:cloudwatch. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:cloudwatch". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by TableName, Operation** — ideal for trending and alerting on this use case.
• Filters the current rows with `where throttled > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throttled requests), Table (table, operation), Single value (throttle bursts per day).

## SPL

```spl
index=aws sourcetype="aws:cloudwatch" namespace="AWS/DynamoDB" metric_name="ThrottledRequests"
| timechart span=5m sum(Sum) as throttled by TableName, Operation
| where throttled > 0
```

## Visualization

Line chart (throttled requests), Table (table, operation), Single value (throttle bursts per day).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
