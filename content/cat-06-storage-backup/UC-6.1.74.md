<!-- AUTO-GENERATED from UC-6.1.74.json — DO NOT EDIT -->

---
id: "6.1.74"
title: "Pure Storage FlashArray capacity forecast with data reduction ratio"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.74 · Pure Storage FlashArray capacity forecast with data reduction ratio

## Description

Forecasting physical utilization alongside data reduction explains whether runway is shrinking because of workload change or weaker dedupe—two very different remediation paths.

## Value

Improves procurement timing and guides workload placement when effective capacity diverges from raw capacity.

## Implementation

Summarize nightly into a summary index for stable `predict`. Document that reduction ratio is a trailing metric; combine with sales forecast tags from a lookup.

## SPL

```spl
index=storage sourcetype="purestorage:array"
| eval used_pct=coalesce(space_percent_used, used_percent, capacity_used_percent)
| eval dr=coalesce(data_reduction, total_reduction, reduction_ratio)
| timechart span=1d latest(used_pct) as used_pct latest(dr) as reduction by array_name
| predict used_pct as forecast future_timespan=30
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

Dual-axis line (used % and reduction), forecast ribbon.

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
