<!-- AUTO-GENERATED from UC-7.4.14.json — DO NOT EDIT -->

---
id: "7.4.14"
title: "Databricks Job Failure Rate"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.4.14 · Databricks Job Failure Rate

## Description

Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

## Value

Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

## Implementation

Ingest each run completion. Alert on any failure for tier-1 jobs; use fail_rate for high-volume jobs. Include `run_page_url` in raw events for triage.

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Databricks job run API, `jobs` audit.
• Ensure the following data sources are available: Job run result (`result_state`, `run_id`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest each run completion. Alert on any failure for tier-1 jobs; use fail_rate for high-volume jobs. Include `run_page_url` in raw events for triage.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=databricks sourcetype="databricks:job_run"
| bin _time span=1d
| stats count(eval(result_state="FAILED")) as failed, count as total by job_name, _time
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 5 OR failed > 0 AND total < 5
| table job_name failed total fail_rate
```

Understanding this SPL

**Databricks Job Failure Rate** — Failed notebook/jar jobs block downstream analytics. Failure rate by job name prioritizes fixes for critical pipelines.

Documented **Data sources**: Job run result (`result_state`, `run_id`). **App/TA** (typical add-on context): Databricks job run API, `jobs` audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: databricks; **sourcetype**: databricks:job_run. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=databricks, sourcetype="databricks:job_run". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by job_name, _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 5 OR failed > 0 AND total < 5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Databricks Job Failure Rate**): table job_name failed total fail_rate


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (failure rate by job), Table (failed runs), Single value (failed jobs 24h).

## SPL

```spl
index=databricks sourcetype="databricks:job_run"
| bin _time span=1d
| stats count(eval(result_state="FAILED")) as failed, count as total by job_name, _time
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 5 OR failed > 0 AND total < 5
| table job_name failed total fail_rate
```

## Visualization

Line chart (failure rate by job), Table (failed runs), Single value (failed jobs 24h).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
