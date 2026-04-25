<!-- AUTO-GENERATED from UC-7.1.75.json — DO NOT EDIT -->

---
id: "7.1.75"
title: "Snowflake Credit Consumption Trending by Warehouse"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.75 · Snowflake Credit Consumption Trending by Warehouse

## Description

Smooth credit trending by warehouse separates organic growth from a runaway job or missing auto-suspend. Comparing each day to a rolling two-week average highlights anomalies before monthly chargeback surprises.

## Value

Lets FinOps and data platform teams intervene on mis-sized warehouses or rogue queries while workloads are still running.

## Implementation

Confirm `CREDITS_USED` and `WAREHOUSE_NAME` field names match your TA version in `props.conf`. Schedule daily aggregation after ACCOUNT_USAGE refresh. Map warehouses to cost centers via lookup. Tune minimum credits (50) per environment.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:warehouse_metering"
| eval wh=coalesce(WAREHOUSE_NAME, warehouse_name)
| eval credits=tonumber(CREDITS_USED)
| bin _time span=1d
| stats sum(credits) as daily_credits by wh, _time
| streamstats window=14 global=f avg(daily_credits) as baseline by wh
| where daily_credits > baseline*1.4 AND daily_credits > 50
```

## Visualization

Line chart (daily_credits vs baseline), Stacked area (top warehouses).

## References

- [Snowflake WAREHOUSE_METERING_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/warehouse_metering_history)
