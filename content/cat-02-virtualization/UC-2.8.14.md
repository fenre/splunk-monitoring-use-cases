<!-- AUTO-GENERATED from UC-2.8.14.json — DO NOT EDIT -->

---
id: "2.8.14"
title: "oVirt User Permission and Role Assignment Audit"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.8.14 · oVirt User Permission and Role Assignment Audit

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Audit, Governance &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Privilege escalations in virtualization are high impact. A searchable history of role grants supports access reviews and insider-threat programs.

## Value

Strengthens least-privilege posture for the virtualization control plane.

## Implementation

Forward immutable audit logs. Join `principal` to HR identity. Alert on new SuperUser assignments.

## SPL

```spl
index=ovirt sourcetype="ovirt:audit" earliest=-30d
| eval act=lower(action)
| where match(act, "(?i)permission|role|admin|add.*user|acl")
| table _time, user, principal, role, object, act
```

## Visualization

Table sorted by time; pivot by role; MLTK rare action optional.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Users and Roles](https://www.ovirt.org/documentation/administration_guide/#chap-Users_and_Roles)
