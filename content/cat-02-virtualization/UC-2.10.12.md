<!-- AUTO-GENERATED from UC-2.10.12.json — DO NOT EDIT -->

---
id: "2.10.12"
title: "VxRail Virtual Machine Storage Policy Mismatch Detection"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.10.12 · VxRail Virtual Machine Storage Policy Mismatch Detection

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance, Data Quality &middot; **Status:** Verified

*We keep an eye on vxRail Virtual Machine Storage Policy Mismatch Detection and raise the alarm before it drags down real work or real outages start.*

---

## Description

Policy drift means VMs may run with lower FTT than the business expects, especially after storage vMotion or restores.

## Value

Aligns guest protection with governance tags and RPO/RTO commitments.

## Implementation

Schedule policy reconciliation. Alert on mismatch. Automate remediation via Storage Policy refresh workflows.

## SPL

```spl
index=vxrail sourcetype="vxrail:vsan_capacity" earliest=-12h
| eval mm=lower(coalesce(mismatch, is_mismatch))
| where mm="true" OR effective_policy!=desired_policy
| stats values(effective_policy) as eff, values(desired_policy) as want by vm_name, cluster_id
```

## Visualization

Table mismatched VMs; count by cluster; trend fixes.

## Known False Positives

IGEL and endpoint UMS health can warn during bulk firmware, certificate rotation, or when a single site loses WAN; use device cohorts to separate local noise from UMS issues.

## References

- [VM storage policies in vSphere](https://www.vmware.com/products/cloud-infrastructure/vsphere)
