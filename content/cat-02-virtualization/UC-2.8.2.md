<!-- AUTO-GENERATED from UC-2.8.2.json — DO NOT EDIT -->

---
id: "2.8.2"
title: "oVirt Host Activation and Maintenance Mode State Changes"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.8.2 · oVirt Host Activation and Maintenance Mode State Changes

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Change, Operations &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Unexpected host activations or maintenance exits change scheduler capacity and can violate change windows. A clear audit of who moved hosts prevents shadow operations.

## Value

Strengthens change governance and speeds incident correlation when capacity drops suddenly.

## Implementation

Ingest host lifecycle events from Engine audit. Build lookups for approved maintenance windows. Alert on transitions outside the window.

## SPL

```spl
index=ovirt sourcetype="ovirt:host" earliest=-24h
| eval ns=lower(coalesce(new_status, status))
| where match(ns, "(?i)maintenance|nonoperational|up|active")
| stats earliest(_time) as first_t, latest(_time) as last_t, values(ns) as statuses by host_name, user
| sort - last_t
```

## Visualization

Timeline per host; table of recent users; single value hosts in maintenance.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Host Administration](https://www.ovirt.org/documentation/administration_guide/)
