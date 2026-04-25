<!-- AUTO-GENERATED from UC-6.2.23.json — DO NOT EDIT -->

---
id: "6.2.23"
title: "Ceph slow OSD requests and op queue latency spikes"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.23 · Ceph slow OSD requests and op queue latency spikes

## Description

Slow requests indicate disk, network, or BlueStore contention on specific OSDs. Aggregating by OSD surfaces hotspots that cluster-wide latency hides.

## Value

Prevents prolonged tail latency for RBD volumes backing databases and VMs.

## Implementation

Tune threshold to cluster size; use percentile summaries for large fleets. Join with `ceph:osd` utilization to separate disk-bound from network-bound cases.

## SPL

```spl
index=os sourcetype="ceph:log" earliest=-4h
| search "slow request" OR "blocked op" OR "op_queue"
| rex field=_raw max_match=1 "(?i)osd\.(?<osd_id>\d+)"
| stats count as slow_ops latest(_time) as last_seen by host, osd_id
| where slow_ops > 20
| sort - slow_ops
```

## Visualization

Bar chart (slow_ops by OSD), timeline.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
