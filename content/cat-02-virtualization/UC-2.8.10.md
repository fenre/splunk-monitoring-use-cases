<!-- AUTO-GENERATED from UC-2.8.10.json — DO NOT EDIT -->

---
id: "2.8.10"
title: "oVirt Template and Snapshot Chain Depth Risk Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.8.10 · oVirt Template and Snapshot Chain Depth Risk Analysis

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

## References

- [oVirt Snapshots](https://www.ovirt.org/documentation/administration_guide/#snapshots)
