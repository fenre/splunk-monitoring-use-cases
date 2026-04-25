<!-- AUTO-GENERATED from UC-6.1.77.json — DO NOT EDIT -->

---
id: "6.1.77"
title: "Pure Storage FlashBlade NFS latency by client and export path"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.77 · Pure Storage FlashBlade NFS latency by client and export path

## Description

NFS hot spots often isolate to a single client or export with aggressive metadata workloads. Client-level latency breaks up array-wide averages that hide real pain.

## Value

Speeds root-cause for HPC and analytics pipelines sharing a single FlashBlade fleet.

## Implementation

Confirm FlashBlade REST exposes per-client NFS metrics; if not, augment with `nfsstat` forwarders on clients for triangulation. Use heavy forwarder for REST polling intervals ≥60s.

## SPL

```spl
index=storage sourcetype="purestorage:array"
| search FlashBlade OR flashblade OR nfs
| eval client=coalesce(nfs_client, client_ip, client)
| eval exp=coalesce(export_path, filesystem, fs_name)
| eval lat_us=coalesce(nfs_latency_usec, op_latency_usec, latency_usec)
| timechart span=5m perc95(lat_us) as p95_usec by client, exp
```

## Visualization

Heatmap (client × export), line chart (p95 latency).

## References

- [Pure Storage Unified Add-on for Splunk (Splunkbase)](https://splunkbase.splunk.com/app/5513)
- [Pure Storage Splunk reference](https://support.purestorage.com/Solutions/Splunk/Splunk_Reference/Array_Monitoring_on_Splunk_with_PureStorage_Unified_App_and_TA)
