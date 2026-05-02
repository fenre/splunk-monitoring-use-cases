<!-- AUTO-GENERATED from UC-6.2.54.json — DO NOT EDIT -->

---
id: "6.2.54"
title: "TrueNAS ZFS resilver progress percent and estimated completion"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.54 · TrueNAS ZFS resilver progress percent and estimated completion

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations, Availability &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Long resilvers extend vulnerability windows to a second disk failure. ETA tracking supports staffing decisions and user communications.

## Value

Reduces panic during RAID-Z repairs by showing evidence-based completion forecasts.

## Implementation

If ETA missing, derive from `bytes_total` and `bytes_processed` deltas using `streamstats`.

## SPL

```spl
index=storage sourcetype="truenas:pool" earliest=-4h
| eval scan_fn=coalesce(scan_function, scan.type)
| where scan_fn="RESILVER" OR match(_raw, "resilver")
| eval pct=coalesce(scan_percent, resilver_percent, progress)
| eval eta=coalesce(estimate_time_remaining_sec, eta_seconds)
| table _time, hostname, pool_name, pct, eta, scan_state
```

## Visualization

Progress bar panel, single value (ETA hours).

## Known False Positives

RAID or vdev state may show degraded briefly during disk replacements before rebuild or resilver progress is reported.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
