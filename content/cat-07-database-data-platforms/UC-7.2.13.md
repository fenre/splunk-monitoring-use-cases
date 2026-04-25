<!-- AUTO-GENERATED from UC-7.2.13.json — DO NOT EDIT -->

---
id: "7.2.13"
title: "MongoDB Atlas Cluster Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.13 · MongoDB Atlas Cluster Alerts

## Description

Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

## Value

Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

## Implementation

Configure Atlas to send alerts to HTTPS endpoint (Splunk HEC) or poll Alerts API every minute. Normalize fields. Page on CRITICAL OPEN alerts.

## Detailed Implementation

Prerequisites
• In operations we confirm in mongosh, MongoDB Compass, or the Atlas metrics UI so replication, elections, and cluster operations match what Splunk shows.
• Install and configure the required add-on or app: MongoDB Atlas API / Atlas App Services webhook, HEC.
• Ensure the following data sources are available: Atlas alert payloads (clusterId, alertType, status, metric values).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Atlas to send alerts to HTTPS endpoint (Splunk HEC) or poll Alerts API every minute. Normalize fields. Page on CRITICAL OPEN alerts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:atlas:alert"
| where status="OPEN" OR severity IN ("CRITICAL","WARNING")
| stats latest(_time) as last_alert, values(alertType) as types by cluster_name, project_id
| sort -last_alert
```

Understanding this SPL

**MongoDB Atlas Cluster Alerts** — Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

Documented **Data sources**: Atlas alert payloads (clusterId, alertType, status, metric values). **App/TA** (typical add-on context): MongoDB Atlas API / Atlas App Services webhook, HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:atlas:alert. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:atlas:alert". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status="OPEN" OR severity IN ("CRITICAL","WARNING")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cluster_name, project_id** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (Atlas alerts), Table (cluster, alert type, status), Single value (open critical count).

## SPL

```spl
index=database sourcetype="mongodb:atlas:alert"
| where status="OPEN" OR severity IN ("CRITICAL","WARNING")
| stats latest(_time) as last_alert, values(alertType) as types by cluster_name, project_id
| sort -last_alert
```

## Visualization

Timeline (Atlas alerts), Table (cluster, alert type, status), Single value (open critical count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
