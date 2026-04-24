---
id: "5.13.53"
title: "Unmanaged or Orphaned Device Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.53 · Unmanaged or Orphaned Device Detection

## Description

Identifies network devices that are managed by Catalyst Center but not assigned to any site in the hierarchy, indicating incomplete provisioning.

## Value

Orphaned devices miss site-specific policies, compliance checks, and reporting groupings. Finding them ensures complete coverage.

## Implementation

Enable the `site_topology` input for site-to-device assignments and the `devicehealth` input for the full managed device list, both targeting `index=catalyst`. Align field names (`deviceId` vs `deviceName`) with your TA extractions; adjust the search if your deployment uses different join keys.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:site:topology (site-to-device assignment) and sourcetype cisco:dnac:devicehealth (total managed device population).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `site_topology` input for site-to-device assignments and the `devicehealth` input for the full managed device list, both targeting `index=catalyst`. Align field names (`deviceId` vs `deviceName`) with your TA extractions; adjust the search if your deployment uses different join keys.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as assigned_devices by siteId, siteName | append [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as total_devices] | eval unassigned=total_devices-assigned_devices | where unassigned > 0 | table siteName assigned_devices total_devices unassigned
```

Understanding this SPL

**Unmanaged or Orphaned Device Detection** — Orphaned devices miss site-specific policies, compliance checks, and reporting groupings. Finding them ensures complete coverage.

**Pipeline walkthrough**

• The main branch tallies `dc(deviceId)` as `assigned_devices` per `siteId` and `siteName` from the topology stream.
• The `append` subsearch pulls a global `dc(deviceName)` as `total_devices` from device health, representing the full managed set.
• `eval` attempts to surface a gap between `total_devices` and per-site `assigned_devices`; you may need to refine this pattern with a proper join in busy environments. `where` keeps rows with positive `unassigned` after evaluation.
• `table` presents the high-level site summary for follow-up in Catalyst Center to locate devices with no site mapping.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (siteName, assigned_devices, total_devices, unassigned), optional follow-on search listing unassigned device names from device health records only.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as assigned_devices by siteId, siteName | append [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as total_devices] | eval unassigned=total_devices-assigned_devices | where unassigned > 0 | table siteName assigned_devices total_devices unassigned
```

## Visualization

Table (siteName, assigned_devices, total_devices, unassigned), optional follow-on search listing unassigned device names from device health records only.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
