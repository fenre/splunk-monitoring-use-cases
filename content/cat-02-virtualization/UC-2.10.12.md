<!-- AUTO-GENERATED from UC-2.10.12.json — DO NOT EDIT -->

---
id: "2.10.12"
title: "VxRail Virtual Machine Storage Policy Mismatch Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.10.12 · VxRail Virtual Machine Storage Policy Mismatch Detection

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

## References

- [VM storage policies in vSphere](https://www.vmware.com/products/cloud-infrastructure/vsphere)
