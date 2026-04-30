<!-- AUTO-GENERATED from UC-2.9.6.json — DO NOT EDIT -->

---
id: "2.9.6"
title: "OpenStack Heat Stack Creation Failures and Rollback Events"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.9.6 · OpenStack Heat Stack Creation Failures and Rollback Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Change &middot; **Status:** Verified

*We monitor the building blocks of your private cloud—computers, networks, disks, and logins—so new systems come up reliably and people are not locked out when something upstream hiccups.*

---

## Description

IaC failures leave partial resources costing money or exposing security gaps. Heat rollbacks should be rare and actionable.

## Value

Improves infrastructure automation reliability and FinOps hygiene.

## Implementation

Parse `status_reason` tokens. Notify project owners on rollback. Trend top failing resources.

## SPL

```spl
index=openstack sourcetype="openstack:heat" earliest=-7d
| eval st=upper(coalesce(status, stack_status))
| where st="FAILED" OR match(st, "ROLLBACK")
| stats count as bad, values(status_reason) as reasons by stack_name, project_id
| sort - bad
```

## Visualization

Bar chart failures by resource type; table stacks; drill to events.

## Known False Positives

OpenStack metrics may swing during image builds, large migrations, or control-plane rolling updates; verify services are healthy in parallel before declaring data-plane failure.

## References

- [OpenStack Heat](https://docs.openstack.org/heat/latest/)
