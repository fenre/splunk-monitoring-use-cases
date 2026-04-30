<!-- AUTO-GENERATED from UC-2.10.6.json — DO NOT EDIT -->

---
id: "2.10.6"
title: "VxRail vSAN Storage Policy Compliance Check Results"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.10.6 · VxRail vSAN Storage Policy Compliance Check Results

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Compliance, Reliability &middot; **Status:** Verified

*We keep an eye on vxRail vSAN Storage Policy Compliance Check Results and raise the alarm before it drags down real work or real outages start.*

---

## Description

Noncompliant objects may lack required FTT during maintenance. This is a leading indicator of impending rebuild stress.

## Value

Ensures data durability matches advertised SLAs before node removals.

## Implementation

Poll compliance after disk or host events. Alert on any noncompliant production VM. Automate owner notification with remediation KB.

## SPL

```spl
index=vxrail sourcetype="vxrail:vsan" earliest=-6h
| eval cs=lower(compliance_state)
| where cs!="compliant"
| stats count as viol, values(policy) as policies by vm_name, cluster_id
```

## Visualization

Bar chart by policy; table VMs; trend violations.

## Known False Positives

IGEL and endpoint UMS health can warn during bulk firmware, certificate rotation, or when a single site loses WAN; use device cohorts to separate local noise from UMS issues.

## References

- [vSAN storage policies](https://www.vmware.com/products/cloud-infrastructure/vsan)
