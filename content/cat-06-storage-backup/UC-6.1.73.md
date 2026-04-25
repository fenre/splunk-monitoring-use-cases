<!-- AUTO-GENERATED from UC-6.1.73.json — DO NOT EDIT -->

---
id: "6.1.73"
title: "Pure Storage protection group replication schedule adherence"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.73 · Pure Storage protection group replication schedule adherence

## Description

Missed replication slots break asynchronous RPO even when instantaneous lag looks fine. Comparing last successful sync to the policy schedule catches silent scheduler failures.

## Value

Protects DR test success rates and contractual RPO reporting for remote protection groups.

## Implementation

Normalize ISO timestamps with `strptime` and timezone. Join expected `cron` schedule from a lookup for precise skew; start with simple 1-hour skew alert.

## SPL

```spl
index=storage (sourcetype="purestorage:array" OR sourcetype="purestorage:volume")
| eval pg=coalesce(protection_group_name, pod_name, pg_name)
| eval last_sync=coalesce(last_replicated_time, last_sync_epoch, last_snapshot_time)
| eval skew_sec=_time-strptime(last_sync, "%Y-%m-%dT%H:%M:%SZ")
| where isnotnull(pg) AND (isnull(last_sync) OR skew_sec > 3600)
| stats latest(last_sync) as last_sync latest(skew_sec) as skew by pg, array_name
| sort - skew
```

## Visualization

Timeline of skew, table (PG, last_sync, skew_sec).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
