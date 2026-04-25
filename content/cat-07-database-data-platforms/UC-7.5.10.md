<!-- AUTO-GENERATED from UC-7.5.10.json — DO NOT EDIT -->

---
id: "7.5.10"
title: "OpenSearch Snapshot / Backup Status"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.5.10 · OpenSearch Snapshot / Backup Status

## Description

Failed or missing snapshots break restore and compliance RPO; monitoring repository and snapshot completion protects against silent backup gaps.

## Value

Failed or missing snapshots break restore and compliance RPO; monitoring repository and snapshot completion protects against silent backup gaps.

## Implementation

Ingest snapshot completion events from `_snapshot/<repo>/_all` or SLM/ISM policy history. Alert on `FAILED` or `PARTIAL` snapshots. Verify last successful snapshot per policy is within SLA (e.g., 24h). Monitor repository connectivity and `read_only` state.

## Detailed Implementation

Prerequisites
• In operations we confirm in OpenSearch Dashboards and `_cat` / `_stats` APIs so index size and merge pressure match what Splunk shows.
• Install and configure the required add-on or app: Custom scripted input (`_snapshot/_status`, `_cat/snapshots`).
• Ensure the following data sources are available: `sourcetype=opensearch:snapshot`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest snapshot completion events from `_snapshot/<repo>/_all` or SLM/ISM policy history. Alert on `FAILED` or `PARTIAL` snapshots. Verify last successful snapshot per policy is within SLA (e.g., 24h). Monitor repository connectivity and `read_only` state.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="opensearch:snapshot"
| eval end_epoch=if(isnotnull(end_time), end_time, _time)
| eval stale=if(state="SUCCESS" AND end_epoch < relative_time(now(),"-25h"),1,0)
| where state IN ("FAILED","PARTIAL") OR stale=1
| table repository, snapshot, state, end_epoch, stale
```

Understanding this SPL

**OpenSearch Snapshot / Backup Status** — Failed or missing snapshots break restore and compliance RPO; monitoring repository and snapshot completion protects against silent backup gaps.

Documented **Data sources**: `sourcetype=opensearch:snapshot`. **App/TA** (typical add-on context): Custom scripted input (`_snapshot/_status`, `_cat/snapshots`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: opensearch:snapshot. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="opensearch:snapshot". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **end_epoch** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **stale** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where state IN ("FAILED","PARTIAL") OR stale=1` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **OpenSearch Snapshot / Backup Status**): table repository, snapshot, state, end_epoch, stale


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (repository, last snapshot, state), Timeline (snapshot jobs), Single value (hours since last success).

## SPL

```spl
index=database sourcetype="opensearch:snapshot"
| eval end_epoch=if(isnotnull(end_time), end_time, _time)
| eval stale=if(state="SUCCESS" AND end_epoch < relative_time(now(),"-25h"),1,0)
| where state IN ("FAILED","PARTIAL") OR stale=1
| table repository, snapshot, state, end_epoch, stale
```

## Visualization

Table (repository, last snapshot, state), Timeline (snapshot jobs), Single value (hours since last success).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
