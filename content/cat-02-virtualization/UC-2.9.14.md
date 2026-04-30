<!-- AUTO-GENERATED from UC-2.9.14.json — DO NOT EDIT -->

---
id: "2.9.14"
title: "OpenStack Placement API Allocation Ratio Threshold Breach"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-2.9.14 · OpenStack Placement API Allocation Ratio Threshold Breach

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Capacity, Risk &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Placement tracks real consumable inventory. Breaching effective capacity risks impossible-to-schedule bursts even when averages look fine.

## Value

Aligns finance and engineering on true headroom before purchase orders land.

## Implementation

Ingest placement summaries per RC. Alert when virtual utilization crosses 95% of effective capacity. Pair with hardware procurement workflow.

## SPL

```spl
index=openstack sourcetype="openstack:placement" earliest=-6h
| eval used=tonumber(allocations_used), inv=tonumber(inventory_total)-tonumber(inventory_reserved)
| eval ar=tonumber(allocation_ratio)
| eval virt_pct=100*used/(inv*ar)
| where virt_pct>95
| stats latest(virt_pct) as pressure by resource_class, hypervisor_hostname
```

## Visualization

Heat map by hypervisor; line chart pressure; table resource classes.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Placement service](https://docs.openstack.org/placement/latest/)
