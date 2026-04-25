<!-- AUTO-GENERATED from UC-2.10.2.json — DO NOT EDIT -->

---
id: "2.10.2"
title: "VxRail Chassis Hardware Component Failure and Predictive Alerts"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.10.2 · VxRail Chassis Hardware Component Failure and Predictive Alerts

## Description

Chassis-level faults can degrade cluster quorum paths and cooling. Surfacing predictive failures schedules proactive swaps before double faults.

## Value

Reduces hardware-induced VM outages and unplanned emergency shipments.

## Implementation

Normalize component taxonomy. Page on critical. Batch predictive weekly for capacity planning.

## SPL

```spl
index=vxrail sourcetype="vxrail:chassis" earliest=-4h
| eval st=lower(state)
| where match(st, "(?i)critical|fail|nonrecover|predictive")
| stats count as alerts, values(component) as parts by serial, redundancy
```

## Visualization

Treemap components; timeline; table serials.

## References

- [VxRail Hardware Administration](https://www.dell.com/support/manuals/en-us/vxrail-products)
