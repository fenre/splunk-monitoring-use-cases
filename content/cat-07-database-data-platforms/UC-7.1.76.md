<!-- AUTO-GENERATED from UC-7.1.76.json — DO NOT EDIT -->

---
id: "7.1.76"
title: "Snowflake Query Queuing Time from Query History"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.76 · Snowflake Query Queuing Time from Query History

## Description

Long queue times before execution mean the warehouse is undersized or overloaded relative to concurrent demand; users experience sluggish dashboards even when executed queries are fast. Separating queue time from execution time targets the right fix (scale-out vs SQL tuning).

## Value

Improves analyst productivity and SLA attainment by resizing warehouses or spreading schedules before executives notice stale data.

## Implementation

Ensure milliseconds fields are ingested as numbers (`QUEUED_OVERLOAD_TIME`, `QUEUED_PROVISIONING_TIME`—names can vary slightly by export; alias in `props.conf`). Filter aborted queries separately. Correlate with `snowflake:warehouse_load` if enabled. Alert per business unit warehouse.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval q_overload=tonumber(QUEUED_OVERLOAD_TIME)
| eval q_prov=tonumber(QUEUED_PROVISIONING_TIME)
| eval queue_ms=coalesce(q_overload,0)+coalesce(q_prov,0)
| where queue_ms > 60000 AND EXECUTION_STATUS="SUCCESS"
| stats median(queue_ms) as p50_queue_ms perc95(queue_ms) as p95_queue_ms count by WAREHOUSE_NAME, USER_NAME
| where p95_queue_ms > 120000
```

## Visualization

Box plot or percentile chart (queue_ms), Table (warehouse, user, p95_queue_ms).

## References

- [Snowflake QUERY_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
