<!-- AUTO-GENERATED from UC-2.8.8.json — DO NOT EDIT -->

---
id: "2.8.8"
title: "oVirt Hot-Plug vCPU and Memory Change Events on Running VMs"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.8.8 · oVirt Hot-Plug vCPU and Memory Change Events on Running VMs

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Capacity &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Hot-plug changes affect capacity planning, licensing, and noisy-neighbor behavior. Centralized visibility prevents untracked resource growth.

## Value

Aligns capacity and finance with actual running configurations.

## Implementation

Parse hotplug audit lines. Feed FinOps dashboards. Alert on large single-step RAM adds in non-prod tenants.

## SPL

```spl
index=ovirt sourcetype="ovirt:vm" earliest=-7d
| eval ac=lower(coalesce(action, operation))
| where match(ac, "(?i)hot.?plug|set.?numa|memory|cpu.*update")
| stats count as changes, sum(vcpu_delta) as vcpu_added, sum(size_mb) as mem_mb_delta by vm_name, user
| sort - changes
```

## Visualization

Bar chart changes by user; table of VMs with deltas.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Resource Usage](https://www.ovirt.org/documentation/administration_guide/#chap-Resource_Usage)
