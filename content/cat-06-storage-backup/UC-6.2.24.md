<!-- AUTO-GENERATED from UC-6.2.24.json — DO NOT EDIT -->

---
id: "6.2.24"
title: "CephFS MDS session cap recall and cache pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.24 · CephFS MDS session cap recall and cache pressure

## Description

Aggressive cap recall usually means clients are hoarding caps or MDS cache is undersized, causing metadata latency for CephFS users.

## Value

Keeps shared filesystems responsive for HPC and EDA workloads without blind MDS reboots.

## Implementation

Split index: `os` for logs, `storage` for JSON status. Add client IP via `rex` when present to notify noisy tenants.

## SPL

```spl
index=os sourcetype="ceph:log" earliest=-4h
| search "mds." AND ("cap" OR "recall" OR "session")
| rex field=_raw "(?i)mds\.(?<mds_id>[a-z0-9_]+)"
| stats count as cap_events by mds_id, host
| where cap_events > 50
| sort - cap_events
```

## Visualization

Table (MDS, events), line chart over time.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
