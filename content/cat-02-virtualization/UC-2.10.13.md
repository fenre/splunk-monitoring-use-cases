<!-- AUTO-GENERATED from UC-2.10.13.json — DO NOT EDIT -->

---
id: "2.10.13"
title: "VxRail vSAN Resync ETA and Throttle Pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.10.13 · VxRail vSAN Resync ETA and Throttle Pressure

## Description

Long resync ETAs after maintenance extend vulnerability windows. Throttle saturation shows contention with production IO.

## Value

Helps operators decide when to pause workloads or widen maintenance windows.

## Implementation

Ingest resync metrics every 5 minutes. Alert when ETA exceeds policy. Compare with `vxrail:vsan_capacity` free chunk balance.

## SPL

```spl
index=vxrail sourcetype="vxrail:vsan" earliest=-6h
| eval remain=tonumber(resync_bytes_remaining)
| eval eta=tonumber(resync_eta_sec)
| where remain>1099511627776 OR eta>86400 OR tonumber(throttle_mbps)<50
| stats latest(remain) as bytes_left, latest(eta) as eta_sec, latest(throttle_mbps) as throttle by cluster_id
```

## Visualization

Area chart bytes remaining; gauge ETA; line chart throttle.

## References

- [vSAN resync and rebuild](https://www.vmware.com/products/cloud-infrastructure/vsan)
