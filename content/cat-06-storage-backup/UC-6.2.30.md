<!-- AUTO-GENERATED from UC-6.2.30.json — DO NOT EDIT -->

---
id: "6.2.30"
title: "Ceph OSD recovery and rebalance throughput versus cluster limits"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.30 · Ceph OSD recovery and rebalance throughput versus cluster limits

## Description

Recovery traffic competes with client IOPS. Monitoring rebalance throughput against configured limits validates throttling and explains user-visible latency during failures.

## Value

Lets operators choose between faster rebuild and application QoS during partial failures.

## Implementation

Parse `progress_events` if available in newer Ceph releases. Join with business-hours lookup to tighten limits interactively.

## SPL

```spl
index=storage sourcetype="ceph:status" earliest=-4h
| eval rbps=coalesce(recovering_bytes_per_sec, recovery_bytes_per_sec, recover_bps)
| eval objs=coalesce(recovering_objects_per_sec, recovery_ops)
| where match(_raw, "recover") OR match(_raw, "rebalanc") OR isnotnull(rbps)
| timechart span=15m max(rbps) as recovery_bps max(objs) as recovery_ops by cluster_name
```

## Visualization

Area chart (recovery Bps), reference line for max osd recovery cap.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
