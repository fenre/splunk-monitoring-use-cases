<!-- AUTO-GENERATED from UC-7.4.18.json — DO NOT EDIT -->

---
id: "7.4.18"
title: "Snowflake Account Storage and Failsafe Footprint"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-7.4.18 · Snowflake Account Storage and Failsafe Footprint

## Description

Rapid growth in storage, stage, or failsafe bytes drives Snowflake bills and retention risk. Finance and platform teams trend ACCOUNT_USAGE storage daily.

## Value

Surfaces runaway tables, clone sprawl, and time-travel/failsafe growth before invoices and disk quotas force emergency purges.

## Implementation

Load STORAGE_USAGE daily per database. Normalize column names to uppercase if using DB Connect. Handle NULL STAGE_BYTES. Join to QUERY_HISTORY for top writers when spikes fire.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:storage_usage"
| eval total_tb=round((STORAGE_BYTES+coalesce(STAGE_BYTES,0)+coalesce(FAILSAFE_BYTES,0))/1099511627776,3)
| timechart span=1d max(total_tb) as total_tb by DATABASE_NAME
| streamstats window=7 avg(total_tb) as baseline by DATABASE_NAME
| where total_tb > baseline*1.25
```

## Visualization

Area chart (TB by component), Table (database, growth %), Single value (account total).

## References

- [Snowflake STORAGE_USAGE view](https://docs.snowflake.com/en/sql-reference/account-usage/storage_usage)
- [DBX Add-on for Snowflake JDBC](https://splunkbase.splunk.com/app/6153)
