<!-- AUTO-GENERATED from UC-6.1.72.json — DO NOT EDIT -->

---
id: "6.1.72"
title: "Pure Storage FlashArray volume snapshot space consumption trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.72 · Pure Storage FlashArray volume snapshot space consumption trending

## Description

Runaway snapshot growth consumes effective capacity and can silently push arrays toward write cliff. Trending snapshot bytes per volume informs retention and offload policies.

## Value

Prevents surprise purchase orders and shortens backup windows by catching snapshot sprawl early.

## Implementation

Ensure REST includes thin provisioning and snapshot breakdown fields. Use `predict` over 30d for capacity forecasting dashboards.

## SPL

```spl
index=storage sourcetype="purestorage:volume"
| eval snap_b=coalesce(space_snapshots, snapshots_bytes, snapshot_space)
| eval data_b=coalesce(space_data, data_bytes, logical_bytes)
| eval snap_pct=if(data_b+snap_b>0, round(snap_b/(data_b+snap_b)*100,2), null())
| timechart span=12h sum(snap_b) as snapshot_bytes by volume_name
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

Area chart (snapshot bytes), table (volume, snap_pct).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
