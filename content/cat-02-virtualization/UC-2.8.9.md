<!-- AUTO-GENERATED from UC-2.8.9.json — DO NOT EDIT -->

---
id: "2.8.9"
title: "oVirt GlusterFS Brick and Volume Health Signals"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.8.9 · oVirt GlusterFS Brick and Volume Health Signals

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Fault &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Gluster-backed domains fail differently than block storage. Brick faults and split-brain signatures need early detection to avoid silent corruption risk.

## Value

Protects distributed storage-backed VMs from prolonged degraded modes.

## Implementation

Ingest gluster health more frequently than generic domain polls. Train operators on heal procedures. Correlate with network partitions.

## SPL

```spl
index=ovirt (sourcetype="ovirt:storagedomain" OR sourcetype="ovirt:gluster") earliest=-1h
| eval st=lower(coalesce(state, brick_state, status))
| where match(st, "(?i)down|faulty|degraded|unknown|out of sync")
| stats latest(_time) as t, values(volume) as vols, values(brick) as bricks by st
| sort - t
```

## Visualization

Map of bricks; timeline degraded state; table volumes.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [GlusterFS with oVirt](https://www.ovirt.org/documentation/administration_guide/#gluster)
