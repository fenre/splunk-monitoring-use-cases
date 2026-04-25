<!-- AUTO-GENERATED from UC-5.13.53.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on for Splunk (7538) with **`site_topology`** (or equivalent) to `cisco:dnac:site:topology` and **`devicehealth`** to `cisco:dnac:devicehealth`, both landing in `index=catalyst`.
• Agree on a single stable device key across streams (`deviceId` from topology vs `deviceName` in health); normalize with `eval` or **props** if the TA uses different field names on each sourcetype.
• `docs/implementation-guide.md` for index routing and input hosts.

Step 1 — Configure data collection
• **Intent API:** site topology and device health are separate TA modular inputs; confirm poll intervals and that both are **enabled** with no `ERROR` in `splunkd.log` on the input host.
• **Catalyst Center** must assign devices to sites for topology events to include membership; unassigned management gear may always appear in health but not in site rolls.

Step 2 — Create the search

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as assigned_devices by siteId, siteName | append [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as total_devices] | eval unassigned=total_devices-assigned_devices | where unassigned > 0 | table siteName assigned_devices total_devices unassigned
```

Understanding this SPL
• This is a **heuristic** gap check: the subsearch is a **fleet-wide** `dc` while the main branch is **per site**; production often replaces `append` with a **summary** or **join** of actual unassigned device lists from a dedicated inventory field in Catalyst Center exports.
• Tune `unassigned>0` only after you prove `deviceId` and `deviceName` (or a unified `deviceId` on both) represent the same population.

**Pipeline walkthrough**
• `dc(deviceId)` by site; `dc(deviceName)` global from health; the difference is **not** mathematically a count of unassigned per row unless you intentionally aggregate — use this as a **signal** to open an inventory report in Catalyst, not as strict accounting without validation.

Step 3 — Validate
• Cross-check counts against **Catalyst Center > Inventory** and **site assignment** in the UI; export a list of unassigned devices from Cisco if the TA exposes that field, and align Splunk.

Step 4 — Operationalize
• Dashboard table for capacity owners; runbook: assign to site, then re-poll and confirm row clears.

Step 5 — Troubleshooting
• **Inflated unassigned:** mixed identifier types; switch both sides to the same UDI or `serialNumber` if indexed.
• **No topology events:** `site_topology` input disabled, wrong site scope, or no device-to-site data for that controller domain.
• **Stagnant `total_devices`:** `devicehealth` poller throttled; compare `dc(deviceName)` in Splunk to fleet size in the UI.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as assigned_devices by siteId, siteName | append [search index=catalyst sourcetype="cisco:dnac:devicehealth" | stats dc(deviceName) as total_devices] | eval unassigned=total_devices-assigned_devices | where unassigned > 0 | table siteName assigned_devices total_devices unassigned
```

## Visualization

Table (siteName, assigned_devices, total_devices, unassigned), optional follow-on search listing unassigned device names from device health records only.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
