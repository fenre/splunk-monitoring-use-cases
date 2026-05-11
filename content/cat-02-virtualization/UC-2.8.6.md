<!-- AUTO-GENERATED from UC-2.8.6.json — DO NOT EDIT -->

---
id: "2.8.6"
title: "oVirt Datacenter and Cluster Maintenance Mode Audit Trail"
status: "verified"
criticality: "medium"
splunkPillar: "Platform"
---

# UC-2.8.6 · oVirt Datacenter and Cluster Maintenance Mode Audit Trail

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Platform &middot; **Type:** Audit, Change &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Cluster-level maintenance disables scheduling safeguards. Auditing who toggled maintenance supports SOX/ITIL evidence and post-incident review.

## Value

Improves accountability for high-blast-radius configuration changes.

## Implementation

Ensure audit retention meets policy. Restrict index access. Schedule weekly digest to infra owners.

## SPL

```spl
index=ovirt sourcetype="ovirt:audit" earliest=-7d
| eval ot=lower(coalesce(object_type, entity_type))
| where ot="datacenter" OR ot="cluster"
| eval act=lower(action)
| where match(act, "(?i)maintenance|activate|deactivate|update")
| table _time, user, object_name, act, before, after
```

## Visualization

Table of changes; timechart by user; filter on production clusters via lookup.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Engine Audit Log](https://www.ovirt.org/develop/developer-guide/engine/)
