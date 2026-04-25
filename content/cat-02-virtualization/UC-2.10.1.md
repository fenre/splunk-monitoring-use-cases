<!-- AUTO-GENERATED from UC-2.10.1.json — DO NOT EDIT -->

---
id: "2.10.1"
title: "VxRail vSAN Disk Group Decommission and Evacuation Events"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.10.1 · VxRail vSAN Disk Group Decommission and Evacuation Events

## Description

Disk group removals trigger large resync traffic. Monitoring decommission status prevents accidental removal during production peaks and validates evacuation completeness.

## Value

Avoids data unavailability during hardware swaps and confirms cluster resilience.

## Implementation

Poll vSAN tasks after each maintenance. Alert on non-success or growing resync bytes. Correlate with `vxrail:physical_disk` SMART events.

## SPL

```spl
index=vxrail sourcetype="vxrail:vsan" earliest=-24h
| eval op=lower(coalesce(operation, op))
| where match(op, "(?i)decom|remove|evac")
| eval st=lower(status)
| where st!="success" OR tonumber(bytes_to_resync)>0
| stats latest(bytes_to_resync) as pending_bytes by cluster_id, disk_group_uuid
```

## Visualization

Timeline decommission; gauge resync bytes; table disk groups.

## References

- [Dell VxRail Support — vSAN operations](https://www.dell.com/support/product-details/product-id.vxrail)
