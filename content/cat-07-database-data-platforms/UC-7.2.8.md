<!-- AUTO-GENERATED from UC-7.2.8.json — DO NOT EDIT -->

---
id: "7.2.8"
title: "Index Build Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.2.8 · Index Build Monitoring

## Description

Index builds consume significant resources and can impact production performance. Tracking ensures builds complete within maintenance windows.

## Value

Index builds consume significant resources and can impact production performance. Tracking ensures builds complete within maintenance windows.

## Implementation

Parse database logs for index build events (start, progress, completion). Alert on index builds in production during business hours. Track build duration for capacity planning.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: Database log parsing.
• Ensure the following data sources are available: MongoDB log (`INDEX` messages), Elasticsearch `_tasks` API.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse database logs for index build events (start, progress, completion). Alert on index builds in production during business hours. Track build duration for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:log"
| search "index build"
| rex "building index on (?<collection>\S+)"
| table _time, host, collection, message
```

Understanding this SPL

**Index Build Monitoring** — Index builds consume significant resources and can impact production performance. Tracking ensures builds complete within maintenance windows.

Documented **Data sources**: MongoDB log (`INDEX` messages), Elasticsearch `_tasks` API. **App/TA** (typical add-on context): Database log parsing. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts fields with `rex` (regular expression).
• Pipeline stage (see **Index Build Monitoring**): table _time, host, collection, message


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (active/recent index builds), Timeline (build events), Single value (builds in progress).

## SPL

```spl
index=database sourcetype="mongodb:log"
| search "index build"
| rex "building index on (?<collection>\S+)"
| table _time, host, collection, message
```

## Visualization

Table (active/recent index builds), Timeline (build events), Single value (builds in progress).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
