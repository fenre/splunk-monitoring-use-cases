<!-- AUTO-GENERATED from UC-6.1.35.json — DO NOT EDIT -->

---
id: "6.1.35"
title: "Pure FlashBlade File System Space Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.35 · Pure FlashBlade File System Space Utilization

## Description

FlashBlade multiprotocol file systems that exceed expected utilization risk writer errors, snapshot failures, and pipeline stalls for analytics and HPC landing zones.

## Value

Provides the same proactive runway discipline as block volumes, but for massive file and small-file workloads where a full filesystem stops entire data pipelines.

## Implementation

Enable file-system inventory inputs on each FlashBlade blade in the Unified Add-on. Map REST `space.virtual` / `space.data` fields into `used_bytes` and `total_bytes` if your TA build uses different keys. Warn at 85% and page at 92% unless the filesystem is a known scratch volume.

## SPL

```spl
index=storage (sourcetype="purestorage:*" OR sourcetype="PureStorage_REST")
| eval used=coalesce(fs_used_bytes, filesystem_used_bytes, used_bytes)
| eval total=coalesce(fs_total_bytes, filesystem_size_bytes, total_bytes)
| eval pct_used=round(used/total*100,2)
| where isnotnull(pct_used) AND pct_used > 85
| stats latest(pct_used) as pct_used latest(used) as used_b latest(total) as total_b by array_name filesystem_name
| sort - pct_used
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

Bar chart (utilization by filesystem), table (top consumers), line chart (7-day growth).

## References

- [Pure Storage Unified App for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5514)
- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
