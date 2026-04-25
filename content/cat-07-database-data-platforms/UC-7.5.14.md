<!-- AUTO-GENERATED from UC-7.5.14.json — DO NOT EDIT -->

---
id: "7.5.14"
title: "Elasticsearch ILM Policy Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.5.14 · Elasticsearch ILM Policy Failures

## Description

Failed ILM transitions leave indices in the wrong lifecycle phase — hot data stays on expensive storage, old data never deletes, rollover stops creating new indices. Silent failures accumulate until disk fills.

## Value

Failed ILM transitions leave indices in the wrong lifecycle phase — hot data stays on expensive storage, old data never deletes, rollover stops creating new indices. Silent failures accumulate until disk fills.

## Implementation

Poll `GET */_ilm/explain` periodically and extract indices where `step` equals `ERROR`. Capture the `failed_step`, `step_info`, and `phase_time` for root cause analysis. Alert on any index stuck in ERROR. Also monitor indices that have been in the same phase longer than expected (e.g., hot phase > 30 days when policy says 7 days).

## Detailed Implementation

Prerequisites
• In operations we confirm in Kibana or OpenSearch Dashboards and the `_cat` / cluster APIs for that stack.
• Install and configure the required add-on or app: Custom REST scripted input (`_ilm/explain`).
• Ensure the following data sources are available: `sourcetype=elasticsearch:ilm_status`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll `GET */_ilm/explain` periodically and extract indices where `step` equals `ERROR`. Capture the `failed_step`, `step_info`, and `phase_time` for root cause analysis. Alert on any index stuck in ERROR. Also monitor indices that have been in the same phase longer than expected (e.g., hot phase > 30 days when policy says 7 days).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="elasticsearch:ilm_status"
| where step="ERROR" OR action_time_millis > 3600000
| stats count as error_count, latest(failed_step) as failed_step, latest(step_info) as reason by index, policy
| sort -error_count
```

Understanding this SPL

**Elasticsearch ILM Policy Failures** — Failed ILM transitions leave indices in the wrong lifecycle phase — hot data stays on expensive storage, old data never deletes, rollover stops creating new indices. Silent failures accumulate until disk fills.

Documented **Data sources**: `sourcetype=elasticsearch:ilm_status`. **App/TA** (typical add-on context): Custom REST scripted input (`_ilm/explain`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: elasticsearch:ilm_status. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="elasticsearch:ilm_status". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where step="ERROR" OR action_time_millis > 3600000` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by index, policy** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (indices in error with reason), Single value (error count), Bar chart (errors by policy).

## SPL

```spl
index=database sourcetype="elasticsearch:ilm_status"
| where step="ERROR" OR action_time_millis > 3600000
| stats count as error_count, latest(failed_step) as failed_step, latest(step_info) as reason by index, policy
| sort -error_count
```

## Visualization

Table (indices in error with reason), Single value (error count), Bar chart (errors by policy).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
