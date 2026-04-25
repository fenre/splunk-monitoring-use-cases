<!-- AUTO-GENERATED from UC-6.2.42.json — DO NOT EDIT -->

---
id: "6.2.42"
title: "TrueNAS ZFS ARC hit ratio and memory pressure trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.42 · TrueNAS ZFS ARC hit ratio and memory pressure trending

## Description

A falling ARC hit ratio on memory-bound appliances raises read latency for NFS and SMB clients even when disks are healthy.

## Value

Guides RAM upgrades and helps distinguish network issues from cache starvation.

## Implementation

If ARC is not in default pool payload, add a lightweight script querying `arcstats` via middleware. Document units in `props.conf`.

## SPL

```spl
index=storage sourcetype="truenas:pool" earliest=-24h
| eval arc_hit=coalesce(arc_hit_ratio, arc_hits_percent, arc_hit_percent)
| eval arc_size=coalesce(arc_size_bytes, arc_size)
| timechart span=15m latest(arc_hit) as arc_hit_pct latest(arc_size) as arc_bytes by hostname
```

## Visualization

Dual-axis line (hit % and ARC bytes).

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
