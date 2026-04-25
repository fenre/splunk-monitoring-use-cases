<!-- AUTO-GENERATED from UC-2.10.4.json — DO NOT EDIT -->

---
id: "2.10.4"
title: "VxRail Firmware and Software Update Compliance Posture"
criticality: "high"
splunkPillar: "Platform"
---

# UC-2.10.4 · VxRail Firmware and Software Update Compliance Posture

## Description

Non-compliant clusters miss security fixes and risk unsupported combinations during VMware upgrades.

## Value

Keeps HCI stacks within Dell support matrices and patch SLAs.

## Implementation

Schedule daily compliance pull. Alert on non-compliant. Integrate with change calendars for staging validation.

## SPL

```spl
index=vxrail sourcetype="vxrail:update" earliest=-24h
| eval comp=lower(compliance_state)
| where comp!="compliant" OR (staged="true" AND installed_release!=target_release)
| stats latest(installed_release) as cur, latest(target_release) as target, latest(comp) as state by cluster_id
```

## Visualization

Matrix table clusters vs target; pie compliance; trend over quarters.

## References

- [VxRail software updates overview](https://www.dell.com/support/manuals/en-us/vxrail-products/vxrail-8.x-software-guide)
