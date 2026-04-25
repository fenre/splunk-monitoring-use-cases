<!-- AUTO-GENERATED from UC-7.5.1.json — DO NOT EDIT -->

---
id: "7.5.1"
title: "Elasticsearch Cluster Health (Red / Yellow)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.1 · Elasticsearch Cluster Health (Red / Yellow)

## Description

Yellow or red cluster status means primary/replica shards are not fully allocated; search and indexing can fail or degrade. Catching status changes early limits user impact.

## Value

Yellow or red cluster status means primary/replica shards are not fully allocated; search and indexing can fail or degrade. Catching status changes early limits user impact.

## Implementation

Poll `GET _cluster/health` every 1–2 minutes and index `status`, `active_primary_shards`, `unassigned_shards`, `number_of_nodes`. Alert immediately on `red` and on sustained `yellow`. Correlate with node loss and disk events.

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom REST scripted input (Elasticsearch `_cluster/health`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:cluster_health`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET _cluster/health` every 1–2 minutes and index `status`, `active_primary_shards`, `unassigned_shards`, `number_of_nodes`. Alert immediately on `red` and on sustained `yellow`. Correlate with node loss and disk events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:cluster_health"
| where status IN ("yellow","red")
| eval severity=if(status="red",3,2)
| timechart span=5m max(severity) as severity by cluster_name
```

Understanding this SPL

**Elasticsearch Cluster Health (Red / Yellow)** — Yellow or red cluster status means primary/replica shards are not fully allocated; search and indexing can fail or degrade. Catching status changes early limits user impact.

Documented **Data sources**: `sourcetype=elasticsearch:cluster_health`. **App/TA** (typical add-on context): Custom REST scripted input (Elasticsearch `_cluster/health`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:cluster_health. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:cluster_health". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status IN ("yellow","red")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **severity** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by cluster_name** — ideal for trending and alerting on this use case.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value or status indicator (cluster status), Line chart (status over time), Table (clusters not green).

## SPL

```spl
index=database sourcetype="elasticsearch:cluster_health"
| where status IN ("yellow","red")
| eval severity=if(status="red",3,2)
| timechart span=5m max(severity) as severity by cluster_name
```

## Visualization

Single value or status indicator (cluster status), Line chart (status over time), Table (clusters not green).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
