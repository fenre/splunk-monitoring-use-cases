<!-- AUTO-GENERATED from UC-7.1.79.json — DO NOT EDIT -->

---
id: "7.1.79"
title: "Snowflake Task Execution Failures and Retries"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.79 · Snowflake Task Execution Failures and Retries

## Description

Failed tasks silently break incremental pipelines—downstream tables stop updating while consumers assume freshness. Clustering failures by task name and schema speeds root-cause analysis across dbt/Snowflake orchestration stacks.

## Value

Prevents stale executive metrics and broken downstream ML features when SQL tasks stop committing.

## Implementation

Map TASK_HISTORY columns (`NAME`, `SCHEMA_NAME`, `DATABASE_NAME`, `STATE`, `ERROR_CODE`, `ERROR_MESSAGE`, `SCHEDULED_TIME`, `COMPLETED_TIME`). Handle retries: dedupe on `QUERY_ID` if present. Link to `snowflake:query_history` for the failing statement text. Maintenance windows via lookup on database/schema.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:task_history"
| where STATE="failed" OR match(upper(coalesce(ERROR_MESSAGE,"")),"ERROR") OR RETURN_VALUE="FAILED"
| eval err=coalesce(ERROR_CODE, ERROR_MESSAGE)
| bin _time span=1h
| stats count as failures values(err) as errors latest(SCHEDULED_TIME) as last_sched by NAME, SCHEMA_NAME, DATABASE_NAME, _time
| where failures >= 3
```

## Visualization

Timeline (failures), Table (task, errors), Sankey to query_id drilldown.

## References

- [Snowflake TASK_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/task_history)
