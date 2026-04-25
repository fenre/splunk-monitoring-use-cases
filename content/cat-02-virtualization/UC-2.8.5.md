<!-- AUTO-GENERATED from UC-2.8.5.json — DO NOT EDIT -->

---
id: "2.8.5"
title: "oVirt Storage Domain Status Transitions (Active/Inactive/Unknown)"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-2.8.5 · oVirt Storage Domain Status Transitions (Active/Inactive/Unknown)

## Description

Storage domains leaving the active state block new disks and snapshots. Unknown states often precede data unavailability for dependent VMs.

## Value

Prevents surprise storage outages and speeds handoff between storage and virtualization teams.

## Implementation

Poll domain status on a short interval. Alert on any non-active production domain. Include `master_domain_version` in the ticket payload.

## SPL

```spl
index=ovirt sourcetype="ovirt:storagedomain" earliest=-24h
| eval ds=lower(status)
| where ds!="active" OR match(lower(_raw), "(?i)unknown|unreachable")
| stats latest(_time) as last_change, latest(status) as cur_status by domain_name
| sort last_change
```

## Visualization

Single value unhealthy domains; timeline; table with version.

## References

- [oVirt Storage Domains](https://www.ovirt.org/documentation/administration_guide/#chap-Storage)
