<!-- AUTO-GENERATED from UC-6.1.66.json — DO NOT EDIT -->

---
id: "6.1.66"
title: "Pure Storage FlashArray host multipath path imbalance detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.66 · Pure Storage FlashArray host multipath path imbalance detection

## Description

Hosts with fewer than two active paths to FlashArray volumes run hot on a single fabric and fail open during HBA or switch maintenance. This is a common misconfiguration after zoning changes.

## Value

Prevents asymmetric multipathing outages and throughput collapse during planned SAN work.

## Implementation

Ensure host inventory REST feed is enabled. If `path_count` is absent, compute from multivalue `target_wwn` or `volume` connection lists via `mvcount` in a scheduled search. Alert integration with CMDB owner field.

## SPL

```spl
index=storage sourcetype="purestorage:host"
| eval paths=coalesce(path_count, active_paths, multipath_paths)
| eval h=coalesce(host_name, hostname, name)
| where isnotnull(h)
| stats latest(paths) as paths values(array_name) as arrays by h
| where paths < 2 OR isnull(paths)
| sort h
```

## Visualization

Table (host, paths, arrays), pie chart (compliant vs non-compliant).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
