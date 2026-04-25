<!-- AUTO-GENERATED from UC-6.1.78.json — DO NOT EDIT -->

---
id: "6.1.78"
title: "Pure Storage FlashBlade S3 bucket capacity and request rate anomalies"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.78 · Pure Storage FlashBlade S3 bucket capacity and request rate anomalies

## Description

Bucket-level growth and request spikes indicate data leaks, misconfigured sync jobs, or abusive clients before capacity or CPU limits trip.

## Value

Protects object storage SLAs for modern apps and data lakes on FlashBlade.

## Implementation

Map Purity//FB REST object counters; if bucket metrics are coarse, aggregate by account with `stats` and alert on week-over-week growth >30%.

## SPL

```spl
index=storage sourcetype="purestorage:array"
| search s3 OR object OR bucket
| eval bucket=coalesce(bucket_name, s3_bucket)
| eval bytes=coalesce(bucket_bytes_used, object_bytes, logical_bytes)
| eval ops=coalesce(s3_ops_per_sec, object_ops, ops_ps)
| timechart span=1h sum(bytes) as bytes latest(ops) as ops by bucket
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (bytes and ops), table (bucket, growth%).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
