<!-- AUTO-GENERATED from UC-6.3.25.json — DO NOT EDIT -->

---
id: "6.3.25"
title: "Pure FlashArray Provisioned Volume Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.25 · Pure FlashArray Provisioned Volume Utilization

## Description

Volumes nearing 100% utilization on FlashArray trigger write failures for databases and VMware datastores even when the physical array still has headroom, because thin provisioning is tracked per volume.

## Value

Aligns host-side capacity runbooks with actual LUN fullness so teams expand volumes or reclaim snapshots before applications hit ENOSPC errors.

## Implementation

Enable volume-level performance/capacity inputs. Map REST `space` objects to `used_bytes`/`total_bytes` if your TA version nests them differently. Warn at 85% and critical at 92% for tier-1 workloads; use a lookup for workload class.

## SPL

```spl
index=storage (sourcetype="purestorage:*" OR sourcetype="PureStorage_REST")
| eval used=coalesce(volume_used_bytes, used_bytes, space_used)
| eval total=coalesce(volume_size_bytes, size_bytes, space_total)
| eval pct_used=round(used/total*100,2)
| where isnotnull(pct_used) AND pct_used > 85
| stats latest(pct_used) as pct_used latest(used) as used_b latest(total) as total_b by array_name volume_name
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

Bar chart (top volumes by %), table (array, volume, TB used).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Unified App for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5514)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
