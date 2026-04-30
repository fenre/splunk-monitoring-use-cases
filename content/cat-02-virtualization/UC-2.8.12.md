<!-- AUTO-GENERATED from UC-2.8.12.json — DO NOT EDIT -->

---
id: "2.8.12"
title: "oVirt MAC Address Pool Utilization and Exhaustion Warning"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-2.8.12 · oVirt MAC Address Pool Utilization and Exhaustion Warning

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Platform &middot; **Type:** Capacity, Risk &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Exhausted MAC pools block new vNICs during scale events. Tracking utilization avoids midnight provisioning failures.

## Value

Prevents automation breakage during burst scaling and lab sprawl.

## Implementation

Export pool stats nightly. Alert above 85% default. Document pool expansion runbook.

## SPL

```spl
index=ovirt (sourcetype="ovirt:audit" OR sourcetype="ovirt:engine") earliest=-24h
| eval used=tonumber(used_macs), tot=tonumber(total_macs)
| eval pct=round(100*used/tot,2)
| where pct>=85 OR match(lower(_raw), "(?i)mac.*pool.*full")
| stats latest(pct) as util_pct by pool_name
```

## Visualization

Gauge utilization; table pools; forecast linear trend.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt MAC Pools](https://www.ovirt.org/documentation/administration_guide/#Mac_Pools)
