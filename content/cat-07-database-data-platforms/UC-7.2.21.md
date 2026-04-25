<!-- AUTO-GENERATED from UC-7.2.21.json — DO NOT EDIT -->

---
id: "7.2.21"
title: "HBase RegionServer Failover Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.21 · HBase RegionServer Failover Events

## Description

RegionServer death and region reassignment cause latency spikes and possible unavailability. Log and metric correlation speeds recovery.

## Value

RegionServer death and region reassignment cause latency spikes and possible unavailability. Log and metric correlation speeds recovery.

## Implementation

Forward HBase master and RS logs. Alert on any dead RS or failed shutdown. Track region-in-transition duration from JMX if ingested.

## Detailed Implementation

Prerequisites
• In operations we confirm in the vendor database console and native system views for the engine this search targets so live metrics match what Splunk shows.
• Install and configure the required add-on or app: HBase Master/RS logs, JMX.
• Ensure the following data sources are available: `ServerShutdownHandler`, `Regions moved`, Dead RegionServer count.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward HBase master and RS logs. Alert on any dead RS or failed shutdown. Track region-in-transition duration from JMX if ingested.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="hbase:master"
| search "ServerShutdownHandler" OR "Dead RegionServer" OR "FailedServerShutdown"
| stats count by cluster_name, host
| where count > 0
```

Understanding this SPL

**HBase RegionServer Failover Events** — RegionServer death and region reassignment cause latency spikes and possible unavailability. Log and metric correlation speeds recovery.

Documented **Data sources**: `ServerShutdownHandler`, `Regions moved`, Dead RegionServer count. **App/TA** (typical add-on context): HBase Master/RS logs, JMX. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: hbase:master. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="hbase:master". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by cluster_name, host** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (RS failures), Table (cluster, host, events), Single value (RS down count).

## SPL

```spl
index=database sourcetype="hbase:master"
| search "ServerShutdownHandler" OR "Dead RegionServer" OR "FailedServerShutdown"
| stats count by cluster_name, host
| where count > 0
```

## Visualization

Timeline (RS failures), Table (cluster, host, events), Single value (RS down count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
