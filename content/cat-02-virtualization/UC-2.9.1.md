<!-- AUTO-GENERATED from UC-2.9.1.json — DO NOT EDIT -->

---
id: "2.9.1"
title: "OpenStack Nova Compute Node vCPU and RAM Allocation Pressure"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.9.1 · OpenStack Nova Compute Node vCPU and RAM Allocation Pressure

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

Hypervisors near CPU or RAM oversubscription limits reject new builds and slow live migrations. Tracking per-host pressure prevents cascading scheduler failures.

## Value

Preserves headroom for failover and burst scaling while controlling noisy-neighbor risk.

## Implementation

Ingest periodic compute capacity JSON. Alert at 90% defaults. Correlate with `openstack:placement` allocation ratios.

## SPL

```spl
index=openstack sourcetype="openstack:nova" earliest=-1h
| eval vcpu_pct=100*tonumber(vcpus_used)/tonumber(vcpus_total)
| eval mem_pct=100*tonumber(memory_mb_used)/tonumber(memory_mb_total)
| where vcpu_pct>90 OR mem_pct>90
| stats latest(vcpu_pct) as vcpu_util, latest(mem_pct) as mem_util by host
```

## Visualization

Dual-axis line chart; heat map by AZ; top 10 hosts table.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Nova — Compute](https://docs.openstack.org/nova/latest/)
