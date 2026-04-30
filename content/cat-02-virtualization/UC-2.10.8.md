<!-- AUTO-GENERATED from UC-2.10.8.json — DO NOT EDIT -->

---
id: "2.10.8"
title: "VxRail Power Supply Redundancy Loss Events"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.10.8 · VxRail Power Supply Redundancy Loss Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Fault, Physical &middot; **Status:** Verified

*We keep an eye on vxRail Power Supply Redundancy Loss Events and raise the alarm before it drags down real work or real outages start.*

---

## Description

Running on a single PSU raises thermal and electrical risk; a second fault can hard-stop a node during peak load.

## Value

Prevents unplanned node loss during maintenance windows and heat waves.

## Implementation

Correlate PSU events with facility tickets. Page on redundancy loss. Track MTTR for PSU replacement.

## SPL

```spl
index=vxrail sourcetype="vxrail:chassis" earliest=-24h
| eval rs=lower(redundancy_state)
| eval h=lower(health)
| where match(rs, "(?i)lost|degraded") OR match(h, "(?i)critical|warning")
| stats latest(redundancy_state) as rs_latest by serial, psu_id
```

## Visualization

Gauge redundancy; timeline; asset table.

## Known False Positives

IGEL and endpoint UMS health can warn during bulk firmware, certificate rotation, or when a single site loses WAN; use device cohorts to separate local noise from UMS issues.

## References

- [Dell PowerEdge power supply health](https://www.dell.com/support/manuals/en-us/poweredge-products)
