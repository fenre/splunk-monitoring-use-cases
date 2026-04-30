<!-- AUTO-GENERATED from UC-6.2.45.json — DO NOT EDIT -->

---
id: "6.2.45"
title: "TrueNAS iSCSI target session disconnect and login failure events"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.45 · TrueNAS iSCSI target session disconnect and login failure events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Status:** Draft

*We help you see how object storage is growing, who can reach it, and when something is exposed or mis-tagged, so cloud storage stays under control.*

---

## Description

Session drops for iSCSI VMs and databases cause filesystem corruption risk and multipath storms. Rapid counts isolate problematic initiators or network paths.

## Value

Protects virtualization clusters using TrueNAS as block storage.

## Implementation

Map TrueNAS alert severities to Splunk severity. If logs lack initiator IQN, augment with switch port counters in a correlated search.

## SPL

```spl
index=storage sourcetype="truenas:alert" earliest=-4h
| search iscsi OR iSCSI OR ctl OR "target offline" OR "session terminate"
| eval tgt=coalesce(target_name, iscsi_target)
| stats count as disc latest(_time) as last_seen by hostname, tgt, initiator
| sort - disc
```

## Visualization

Timeline, table (target, initiator, count).

## Known False Positives

Short spikes during approved changes, maintenance windows, or known batch jobs can match the rule; confirm against the vendor console and change calendar.

## References

- [TrueNAS SCALE API documentation](https://www.truenas.com/docs/scale/scaletutorials/toptoolbar/reportinggraphs/)
- [TrueNAS CORE/SCALE docs — alerts](https://www.truenas.com/docs/)
