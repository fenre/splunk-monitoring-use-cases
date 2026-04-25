<!-- AUTO-GENERATED from UC-6.1.67.json — DO NOT EDIT -->

---
id: "6.1.67"
title: "Pure Storage FlashArray volume QoS bandwidth and IOPS limit enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.67 · Pure Storage FlashArray volume QoS bandwidth and IOPS limit enforcement

## Description

Workloads pinned at QoS ceilings experience tail latency and application time-outs even when the array has spare headroom. Detecting sustained ceiling hits validates policy vs reality.

## Value

Aligns storage QoS with application SLAs and documents when limits—not hardware—are the bottleneck.

## Implementation

Enable volume performance REST collection. Map Purity fields to `qos_*` names with `FIELDALIAS`. Create separate alerts for bursty vs sustained (15m `perc90`) saturation.

## SPL

```spl
index=storage sourcetype="purestorage:volume"
| eval bw_cap=coalesce(qos_bandwidth_limit_mbps, bandwidth_limit_mbps)
| eval iops_cap=coalesce(qos_iops_limit, iops_limit)
| eval bw_use=coalesce(bandwidth_mbps, read_bw_mbps+write_bw_mbps)
| eval iops_use=coalesce(total_iops, read_iops+write_iops)
| where (isnotnull(bw_cap) AND bw_use >= 0.95*bw_cap) OR (isnotnull(iops_cap) AND iops_use >= 0.95*iops_cap)
| table _time, array_name, volume_name, bw_cap, bw_use, iops_cap, iops_use
```

## Visualization

Timechart of utilization vs cap, table of volumes at ceiling.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
