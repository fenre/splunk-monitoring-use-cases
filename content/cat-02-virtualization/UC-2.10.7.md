<!-- AUTO-GENERATED from UC-2.10.7.json — DO NOT EDIT -->

---
id: "2.10.7"
title: "VxRail Cluster Node Add and Remove Operations Audit"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.10.7 · VxRail Cluster Node Add and Remove Operations Audit

## Description

Unauthorized or failed node operations change failure domains. A tamper-evident history supports SOX-style change evidence.

## Value

Improves cluster integrity assurance and speeds forensic review.

## Implementation

Forward immutable audit logs. Join users to corporate directory. Alert on remove attempts without change ticket lookup match.

## SPL

```spl
index=vxrail sourcetype="vxrail:system" earliest=-30d
| eval op=lower(operation)
| where match(op, "(?i)add|remove|expand|shrink")
| table _time, cluster_id, node_serial, op, status, user
```

## Visualization

Timeline; user pivot; export CSV for CAB.

## References

- [VxRail cluster expansion](https://www.dell.com/support/manuals/en-us/vxrail-products)
