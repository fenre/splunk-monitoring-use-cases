<!-- AUTO-GENERATED from UC-6.3.26.json — DO NOT EDIT -->

---
id: "6.3.26"
title: "Ceph Cluster OSD nearfull and full Capacity Flags"
status: "draft"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.3.26 · Ceph Cluster OSD nearfull and full Capacity Flags

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Availability &middot; **Status:** Draft

*We watch how full your storage is getting and give you time to add space or clean up snapshots and old data before an application or job suddenly stops working.*

---

## Description

When too many OSDs cross `nearfull` or `full` thresholds, Ceph stops accepting client writes to affected pools—an operational outage distinct from generic `HEALTH_WARN` text.

## Value

Gives storage SREs a dedicated alert for capacity-induced write suppression so they can expand the cluster or reweight OSDs before applications freeze.

## Implementation

Ensure your JSON parser preserves `health.checks` messages or the stringified `health_detail` blob containing `nearfull`. If using Prometheus instead, map `ceph_osd_nearfull` gauges into Splunk metrics and mirror this logic with `mstats`. Pair with UC-6.1.14 for overall health.

## SPL

```spl
index=storage sourcetype="ceph:status" earliest=-30m
| search "nearfull" OR "full" OR "backfillfull"
| eval flag=coalesce(health_detail, summary, health_summary)
| stats latest(_time) as last_seen latest(health) as health latest(flag) as detail latest(osd_up) as osd_up latest(osd_in) as osd_in by cluster_name
| sort - last_seen
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Single value (clusters in nearfull), table (cluster, detail), link to OSD utilization dashboard.

## Known False Positives

Backfill and rebalancing after node changes can move the cluster toward full before new capacity is absorbed; check recovery and CRUSH activity in the cluster manager.

## References

- [Ceph Documentation — Monitoring OSDs](https://docs.ceph.com/en/latest/rados/operations/)
- [Ceph Documentation — Full OSDs](https://docs.ceph.com/en/latest/rados/operations/add-or-rm-osds/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
