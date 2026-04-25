<!-- AUTO-GENERATED from UC-7.1.80.json — DO NOT EDIT -->

---
id: "7.1.80"
title: "Snowflake Query Spill to Remote Storage Ratio"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.1.80 · Snowflake Query Spill to Remote Storage Ratio

## Description

Remote spill is particularly expensive and slow compared with in-memory execution; a high spill-to-scan ratio flags queries that need warehouse sizing, clustering, or predicate fixes before they become recurring credit burners.

## Value

Cuts Snowflake cost and latency by targeting the worst remote spill offenders with engineering fixes.

## Implementation

Verify spill columns exist in your Snowflake edition export. Null-safe `tonumber()` in SPL. Exclude ETL service accounts with known wide aggregates via lookup. Dashboard top 20 queries weekly; alert when any single execution exceeds 1GB remote spill and 5% ratio.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:query_history"
| eval remote_spill=tonumber(BYTES_SPILLED_TO_REMOTE_STORAGE)
| eval local_spill=tonumber(BYTES_SPILLED_TO_LOCAL_STORAGE)
| eval scanned=tonumber(BYTES_SCANNED)
| eval spill_ratio=if(scanned>0, round((remote_spill+local_spill)/scanned*100,2), null())
| where remote_spill > 1073741824 AND spill_ratio > 5
| stats sum(remote_spill) as total_remote sum(scanned) as total_scanned values(QUERY_TEXT) as sample_sql by USER_NAME, WAREHOUSE_NAME
| sort -total_remote
```

## Visualization

Bar chart (total_remote by user), Table (sample_sql truncated).

## References

- [Snowflake — Spilling](https://docs.snowflake.com/en/user-guide/ui-query-profile#spilling)
