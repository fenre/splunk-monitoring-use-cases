<!-- AUTO-GENERATED from UC-6.2.47.json — DO NOT EDIT -->

---
id: "6.2.47"
title: "TrueNAS NFS export latency and RPC slow operations"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.47 · TrueNAS NFS export latency and RPC slow operations

## Description

Per-client NFS latency distinguishes overloaded clients from array-side CPU or ZIL contention affecting many hosts.

## Value

Speeds remediation for EDA and render farms using NFS on TrueNAS.

## Implementation

If only server-side stats exist, pair with client `nfsiostat` forwarders for triangulation. Tag exports with workload class via lookup.

## SPL

```spl
index=storage (sourcetype="truenas:pool" OR sourcetype="truenas:alert")
| search nfs OR NFS
| eval client=coalesce(client_ip, nfs_client)
| eval lat_ms=coalesce(nfs_latency_ms, rpc_latency_ms)
| timechart span=5m perc95(lat_ms) as p95_ms by client, export_path
```

## Visualization

Heatmap client × export, line chart p95.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
