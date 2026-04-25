<!-- AUTO-GENERATED from UC-6.2.27.json — DO NOT EDIT -->

---
id: "6.2.27"
title: "Ceph RBD mirror image replay lag and split-brain flags"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.27 · Ceph RBD mirror image replay lag and split-brain flags

## Description

RBD mirroring protects block workloads across clusters; replay lag or split-brain states mean DR copies are not trustworthy until repaired.

## Value

Preserves block storage RPO for VMware and OpenStack estates using Ceph RBD.

## Implementation

Run mirror status commands under least-privilege keyring. Redact image names with PHI via `SED` in transforms if needed.

## SPL

```spl
index=storage (sourcetype="ceph:pool" OR sourcetype="ceph:status")
| search rbd OR mirror
| eval lag_sec=coalesce(replay_lag_seconds, bytes_behind, lag_seconds)
| eval state=coalesce(mirror_state, state)
| where match(state, "(?i)error|split|stuck") OR lag_sec > 300
| stats max(lag_sec) as max_lag latest(state) as mirror_state by image_name, cluster_name
| sort - max_lag
```

## Visualization

Table (image, lag, state), timeline.

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
