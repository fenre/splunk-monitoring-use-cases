<!-- AUTO-GENERATED from UC-6.2.22.json — DO NOT EDIT -->

---
id: "6.2.22"
title: "Ceph monitor quorum loss and election storm detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.2.22 · Ceph monitor quorum loss and election storm detection

## Description

Monitor quorum loss freezes cluster configuration updates and often precedes client I/O issues. Detecting partial quorum early preserves metadata safety.

## Value

Protects RBD, CephFS, and RGW control-plane operations during rack or site failures.

## Implementation

Ingest `ceph quorum_status` JSON every minute during incidents (5 minutes steady state). Correlate with `ceph:log` from mon hosts for clock or disk issues.

## SPL

```spl
index=storage (sourcetype="ceph:health" OR sourcetype="ceph:status")
| eval quorum=coalesce(quorum_names, quorum, mon_quorum)
| eval qsize=coalesce(quorum_size, mvcount(split(quorum,",")))
| eval mons=coalesce(mon_total, num_mons)
| where isnotnull(mons) AND (qsize < ceil(mons/2)+1 OR match(_raw, "quorum"))
| search NOT HEALTH_OK OR qsize < 2
| table _time, cluster_name, quorum, mons, health_detail
```

## Visualization

Timeline of quorum size, table (cluster, detail).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
