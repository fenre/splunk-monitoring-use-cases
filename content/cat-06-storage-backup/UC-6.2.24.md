<!-- AUTO-GENERATED from UC-6.2.24.json — DO NOT EDIT -->

---
id: "6.2.24"
title: "CephFS MDS session cap recall and cache pressure"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.24 · CephFS MDS session cap recall and cache pressure

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Status:** Draft

*We watch who is allowed on the storage network and who just logged in, so stray servers or surprise changes on the fabric are harder to miss.*

---

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

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
