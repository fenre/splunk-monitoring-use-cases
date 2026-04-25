<!-- AUTO-GENERATED from UC-7.6.6.json — DO NOT EDIT -->

---
id: "7.6.6"
title: "Snowflake Columnar Access History for Sensitive Objects"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.6.6 · Snowflake Columnar Access History for Sensitive Objects

## Description

ACCESS_HISTORY shows which columns were read; mapping those events to a sensitive-object inventory is a common Snowflake governance pattern for GDPR/PCI reviews.

## Value

Produces auditor-friendly evidence of who touched regulated columns without relying solely on warehouse-native reports.

## Implementation

Maintain `sensitive_snowflake_objects.csv` (database, schema, object, column). Schedule ACCESS_HISTORY pulls with acceptable latency. Mask direct identifiers in Splunk if required. Document retention on the evidence index.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:access_history"
| lookup sensitive_snowflake_objects object_name OUTPUT is_pii
| where is_pii=1
| stats dc(QUERY_ID) as queries dc(USER_NAME) as actors values(OBJECT_MODIFIED_BY_DDL) as ddl_flag by OBJECT_NAME, _time
| where queries > 0
```

## Visualization

Table (object, users, query count), Timeline (access), Heatmap (roles).

## References

- [Snowflake ACCESS_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/access_history)
- [DBX Add-on for Snowflake JDBC](https://splunkbase.splunk.com/app/6153)
