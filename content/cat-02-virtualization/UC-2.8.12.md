<!-- AUTO-GENERATED from UC-2.8.12.json — DO NOT EDIT -->

---
id: "2.8.12"
title: "oVirt MAC Address Pool Utilization and Exhaustion Warning"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-2.8.12 · oVirt MAC Address Pool Utilization and Exhaustion Warning

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

## References

- [oVirt MAC Pools](https://www.ovirt.org/documentation/administration_guide/#Mac_Pools)
