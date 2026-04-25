<!-- AUTO-GENERATED from UC-7.4.3.json — DO NOT EDIT -->

---
id: "7.4.3"
title: "Data Pipeline Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.4.3 · Data Pipeline Health

## Description

Failed or delayed ETL/ELT pipelines cause stale data for reporting and analytics. Early detection prevents downstream impact.

## Value

Failed or delayed ETL/ELT pipelines cause stale data for reporting and analytics. Early detection prevents downstream impact.

## Implementation

Ingest pipeline orchestrator logs (Airflow, dbt, custom). Track job outcomes, durations, and data freshness. Alert on any pipeline failure. Create data freshness SLA dashboard showing when each table was last updated. For dbt and Snowflake pipelines, create similar searches targeting their respective sourcetypes (e.g., snowflake:task_history, dbt:run_results).

## Detailed Implementation

Prerequisites
• In operations we confirm in pgAdmin, psql, and `pg_stat*` views, or the managed PostgreSQL console.
• Install and configure the required add-on or app: Custom API input, orchestrator integration (Airflow, dbt).
• Ensure the following data sources are available: Airflow task logs, dbt run results, Snowflake TASK_HISTORY, pipeline orchestrator APIs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest pipeline orchestrator logs (Airflow, dbt, custom). Track job outcomes, durations, and data freshness. Alert on any pipeline failure. Create data freshness SLA dashboard showing when each table was last updated. For dbt and Snowflake pipelines, create similar searches targeting their respective sourcetypes (e.g., snowflake:task_history, dbt:run_results).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=datawarehouse sourcetype="airflow:task_instance"
| stats count(eval(state="failed")) as failed, count(eval(state="success")) as success, count as total by dag_id, task_id
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 0
| sort -fail_rate
```

Understanding this SPL

**Data Pipeline Health** — Failed or delayed ETL/ELT pipelines cause stale data for reporting and analytics. Early detection prevents downstream impact.

Documented **Data sources**: Airflow task logs, dbt run results, Snowflake TASK_HISTORY, pipeline orchestrator APIs. **App/TA** (typical add-on context): Custom API input, orchestrator integration (Airflow, dbt). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: datawarehouse; **sourcetype**: airflow:task_instance. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=datawarehouse, sourcetype="airflow:task_instance". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dag_id, task_id** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **fail_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where fail_rate > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
For the same time range, compare Splunk results with the engine’s own tools and system views (SQL Server: SQL Server Management Studio and `sys.dm_*`; Oracle: Oracle Enterprise Manager, SQLcl, or `V$` views; MySQL: Workbench or `performance_schema` / `SHOW` output; PostgreSQL: `pg_stat_*` in psql or pgAdmin; MongoDB: mongosh or Atlas metrics; Cassandra: nodetool; Elasticsearch/OpenSearch: Kibana or REST `_cat` / `_cluster/health`; ClickHouse: `system` tables in clickhouse-client; Snowflake: Snowsight or `ACCOUNT_USAGE`; others: the managed PaaS console). Confirm event counts, field names, timestamps, and Splunk role permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (pipeline × status), Table (failed pipelines), Line chart (pipeline duration trend), Single value (overall success rate).

## SPL

```spl
index=datawarehouse sourcetype="airflow:task_instance"
| stats count(eval(state="failed")) as failed, count(eval(state="success")) as success, count as total by dag_id, task_id
| eval fail_rate=round(failed/total*100,1)
| where fail_rate > 0
| sort -fail_rate
```

## Visualization

Status grid (pipeline × status), Table (failed pipelines), Line chart (pipeline duration trend), Single value (overall success rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
