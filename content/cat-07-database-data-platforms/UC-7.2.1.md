<!-- AUTO-GENERATED from UC-7.2.1.json — DO NOT EDIT -->

---
id: "7.2.1"
title: "Cluster Membership Changes"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.1 · Cluster Membership Changes

## Description

Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

## Value

Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

## Implementation

Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: Custom scripted input, database event logs.
• Ensure the following data sources are available: MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward database logs to Splunk. Parse membership change events. Alert on unexpected node departures. For Elasticsearch, poll `_cluster/health` API and alert on node count changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```

Understanding this SPL

**Cluster Membership Changes** — Node additions/removals affect data distribution and availability. Unexpected membership changes may indicate failures.

Documented **Data sources**: MongoDB replica set events, Cassandra `system.log`, Elasticsearch cluster state. **App/TA** (typical add-on context): Custom scripted input, database event logs. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:log. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:log". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Cluster Membership Changes**): table _time, host, message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (membership events), Single value (current node count), Table (recent cluster changes).

## SPL

```spl
index=database sourcetype="mongodb:log"
| search "replSet" ("added" OR "removed" OR "changed state" OR "election")
| table _time, host, message
| sort -_time
```

## Visualization

Timeline (membership events), Single value (current node count), Table (recent cluster changes).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
