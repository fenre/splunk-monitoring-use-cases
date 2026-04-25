<!-- AUTO-GENERATED from UC-7.5.22.json — DO NOT EDIT -->

---
id: "7.5.22"
title: "Snowflake Schema Object DDL from Query History"
criticality: "medium"
splunkPillar: "IT Operations"
---

# UC-7.5.22 · Snowflake Schema Object DDL from Query History

## Description

Tracking DDL executed in Snowflake supports change governance: who created pipes, stages, or tables outside CAB windows. ACCOUNT_USAGE query history is the standard audit source.

## Value

Improves forensic reconstruction after incidents and enforces separation-of-duties on production accounts.

## Implementation

Replicate QUERY_HISTORY on a schedule (note ACCOUNT_USAGE latency). Filter to production roles. Join QUERY_ID to ACCESS_HISTORY if column-level detail is required. Archive results to a restricted index.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| search QUERY_TYPE="DDL" OR match(QUERY_TEXT,"(?i)^(create|alter|drop)\s+(table|view|schema|warehouse|pipe|stage|task|stream)")
| stats earliest(_time) as first_seen latest(QUERY_TEXT) as ddl latest(USER_NAME) as actor by QUERY_ID
| table first_seen actor ddl
```

## Visualization

Table (time, actor, statement), Timeline (DDL volume), Top users.

## References

- [Snowflake QUERY_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
- [DBX Add-on for Snowflake JDBC](https://splunkbase.splunk.com/app/6153)
