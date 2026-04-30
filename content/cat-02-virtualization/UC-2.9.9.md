<!-- AUTO-GENERATED from UC-2.9.9.json — DO NOT EDIT -->

---
id: "2.9.9"
title: "OpenStack Nova Instance State Stuck in BUILD or ERROR"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-2.9.9 · OpenStack Nova Instance State Stuck in BUILD or ERROR

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Fault, Availability &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Instances stuck mid-build consume quotas and mask scheduler or image issues. Long-lived ERROR states often indicate recurring hardware faults.

## Value

Protects tenant SLAs and prevents ghost capacity consumption.

## Implementation

Snapshot state every few minutes. Alert when age exceeds 15 minutes. Auto-open tickets with hypervisor and image id.

## SPL

```spl
index=openstack sourcetype="openstack:nova" earliest=-6h
| eval vs=lower(coalesce(vm_state, state))
| eval ts=lower(coalesce(task_state, task))
| where vs="build" OR vs="error" OR match(ts, "(?i)scheduling|networking|block_device")
| eval age_sec=now()-tonumber(state_changed_epoch)
| where age_sec>900
| stats max(age_sec) as max_age by instance_uuid, host, vs
```

## Visualization

Single value stuck count; table oldest instances; timeline transitions.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Nova Instance States](https://docs.openstack.org/nova/latest/reference/vm-states.html)
