<!-- AUTO-GENERATED from UC-7.1.60.json — DO NOT EDIT -->

---
id: "7.1.60"
title: "ClickHouse Per-Query Memory Usage and OOM Risk"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.1.60 · ClickHouse Per-Query Memory Usage and OOM Risk

## Description

Runaway `peak_memory_usage` on a few queries is the usual precursor to server-wide OOM kills under concurrent load. Tracking peak memory by `user` and `host` lets you enforce query limits and isolate bad SQL before the process restarts.

## Value

Stabilizes shared analytics clusters and avoids surprise restarts during month-end reporting peaks.

## Implementation

Confirm `peak_memory_usage` is present in your `query_log` version; add `max_memory_usage_for_user` policies in ClickHouse for prevention. In Splunk, schedule alert for peak_mb above tenant-specific limits (example 1GB). Join with LDAP/group lookup for chargeback.

## SPL

```spl
index=database sourcetype="clickhouse:query_log"
| eval mem_mb=round(tonumber(peak_memory_usage)/1048576,1)
| where mem_mb > 1024 OR match(_raw,"MEMORY_LIMIT_EXCEEDED")
| stats max(mem_mb) as peak_mb sum(read_rows) as rows values(query_id) as qids by user, host
| sort -peak_mb
```

## Visualization

Bar chart (peak_mb by user), Table (qids, rows, peak_mb).

## References

- [ClickHouse — Memory limit settings](https://clickhouse.com/docs/en/operations/settings/query-complexity#settings_max_memory_usage)
