<!-- AUTO-GENERATED from UC-6.2.48.json — DO NOT EDIT -->

---
id: "6.2.48"
title: "TrueNAS UPS battery runtime remaining and power failover readiness"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.48 · TrueNAS UPS battery runtime remaining and power failover readiness

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Physical &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Short UPS runtime risks unclean shutdown of ZFS pools during extended outages, risking import failures and long scrubs.

## Value

Triggers orderly shutdown automation and vendor dispatch before batteries are exhausted.

## Implementation

Normalize UPS names across sites. Test syslog formats from `upsmon` after firmware upgrades.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-30m
| search UPS OR NUT OR battery OR onbatt
| eval minutes=coalesce(battery_runtime_minutes, runtime_min, time_left_min)
| where minutes < 10 OR match(_raw, "on battery|OB ")
| stats latest(minutes) as runtime_min by hostname, ups_name
```

## Visualization

Single value (min runtime), table (site, UPS).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
