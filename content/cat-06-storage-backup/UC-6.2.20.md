<!-- AUTO-GENERATED from UC-6.2.20.json — DO NOT EDIT -->

---
id: "6.2.20"
title: "Ceph cluster OSD nearfull and backfillfull capacity pressure"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.20 · Ceph cluster OSD nearfull and backfillfull capacity pressure

## Description

OSDs approaching nearfull or backfillfull slow rebalancing and risk write failures during recovery. Per-OSD utilization highlights imbalanced CRUSH weights or failed additions.

## Value

Prevents cluster-wide ingest stalls and gives operators time to expand before PGs cannot backfill.

## Implementation

Run `ceph osd df -f json` every 5 minutes via scripted input; flatten `nodes` array into one event per OSD. Set `props.conf` for `ceph:osd`. Page when util > 85% for any OSD class serving production pools.

## SPL

```spl
index=storage sourcetype="ceph:osd" earliest=-30m
| eval util=coalesce(utilization, pcent, space_used_percent)
| where util > 85 OR state="nearfull" OR state="backfillfull" OR match(_raw, "nearfull|backfillfull")
| stats max(util) as max_util values(state) as states by osd_id, cluster_name
| sort - max_util
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

Bar chart (util by OSD), table (osd_id, util, host).

## References

- [Ceph Documentation — monitoring](https://docs.ceph.com/en/latest/radosgw/)
- [Red Hat Ceph Storage — troubleshooting](https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
