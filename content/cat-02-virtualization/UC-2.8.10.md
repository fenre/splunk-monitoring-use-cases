<!-- AUTO-GENERATED from UC-2.8.10.json — DO NOT EDIT -->

---
id: "2.8.10"
title: "oVirt Template and Snapshot Chain Depth Risk Analysis"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.8.10 · oVirt Template and Snapshot Chain Depth Risk Analysis

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Capacity, Performance &middot; **Status:** Verified

*We keep an eye on the control panel that runs your virtual datacenter—who changed what, whether storage and hosts are healthy, and when something is about to strand running machines.*

---

## Description

Deep snapshot chains slow reads and complicate backups. Identifying VMs over policy thresholds guides consolidation windows.

## Value

Reduces I/O latency surprises and shortens backup windows.

## Implementation

Schedule daily inventory. Alert when `chain_depth` exceeds internal standard. Automate emails to VM owners with merge instructions.

## SPL

```spl
index=ovirt sourcetype="ovirt:vm" earliest=-1d
| eval depth=tonumber(coalesce(chain_depth, snapshot_count))
| where depth>4
| stats max(depth) as max_depth, values(base_image_id) as bases by vm_name
| sort - max_depth
```

## Visualization

Histogram of depths; table worst VMs; trend over weeks.

## Known False Positives

AOS storage metrics can look worse during background heal, curator, or disk removal work; match alerts to Nutanix task progress and maintenance windows.

## References

- [oVirt Snapshots](https://www.ovirt.org/documentation/administration_guide/#snapshots)
