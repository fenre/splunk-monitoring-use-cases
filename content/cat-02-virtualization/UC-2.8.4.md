<!-- AUTO-GENERATED from UC-2.8.4.json — DO NOT EDIT -->

---
id: "2.8.4"
title: "oVirt VM Migration Failures and Timeout Events"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.8.4 · oVirt VM Migration Failures and Timeout Events

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Fault &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Failed migrations leave VMs on stressed hosts or mid-maintenance. Timeouts often indicate saturated migration networks or storage pressure.

## Value

Keeps maintenance and evacuation projects safe and reduces user-visible pauses.

## Implementation

Extract migration failure reasons. Alert on any failure in production clusters. Trend top reasons weekly for engineering backlog.

## SPL

```spl
index=ovirt sourcetype="ovirt:vm" earliest=-24h
| eval st=lower(coalesce(status, migration_status))
| where match(st, "(?i)fail|error|timeout|cancel")
| eval reason=coalesce(reason, fail_reason, message)
| stats count as fails, values(reason) as reasons, values(dst_host) as targets by vm_name, src_host
| sort - fails
```

## Visualization

Pie of failure reasons; table vm/host; timechart failure rate.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Migrating Virtual Machines](https://www.ovirt.org/documentation/administration_guide/#sect-Migrating_virtual_machines)
