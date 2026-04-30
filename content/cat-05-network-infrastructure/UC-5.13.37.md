<!-- AUTO-GENERATED from UC-5.13.37.json — DO NOT EDIT -->

---
id: "5.13.37"
title: "Devices Affected by Active Advisories"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.37 · Devices Affected by Active Advisories

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability &middot; **Wave:** Walk &middot; **Status:** Verified

*We list exactly which network devices are affected by each security weakness, so your team knows precisely which boxes need a software update — not just 'we have a vulnerability' but 'these 12 specific switches in Building A need to be upgraded to version 17.9.4a.'*

---

## Description

Lists every device affected by each active security advisory, showing which specific switches, routers, and WLCs need firmware upgrades or workarounds — transforming the abstract advisory count from UC-5.13.34 into a concrete device-level remediation plan.

## Value

UC-5.13.34 says '5 CRITICAL advisories affect 47 devices.' This UC says WHICH 47 devices, what firmware they're running, and what version they need. That's the difference between a vulnerability report and a remediation work order. The per-device list is what the firmware upgrade team needs to build the SWIM distribution plan in Catalyst Center, and what the security team needs for risk-based prioritisation (internet-facing core switch vs. internal access switch).

## Implementation

Same `securityadvisory` input as UC-5.13.34. The API should return device-level data within advisory events. If device IDs are returned instead of names, join with `index=catalyst sourcetype="cisco:dnac:device"` for hostname enrichment.

## Detailed Implementation

### Prerequisites
- UC-5.13.34 (PSIRT Overview) must be operational — same `securityadvisory` data feed.
- For device name enrichment, maintain a `catalyst_device_lookup` from the device inventory input: `index=catalyst sourcetype="cisco:dnac:device" | stats latest(hostname) as deviceName latest(platformId) as platformId latest(softwareVersion) as softwareVersion by id | rename id as deviceId | outputlookup catalyst_device_lookup`. Schedule this daily.
- This UC transforms the abstract advisory count from UC-5.13.34 into a concrete device-level remediation plan. The output is what the firmware upgrade team needs to build the SWIM distribution task in Catalyst Center.

### Step 1 — Configure data collection
Same `securityadvisory` input as UC-5.13.34. The API returns advisory-to-device mappings — each event links an `advisoryId` to affected devices via `deviceId` or `deviceCount`.

Note: the level of per-device detail in the advisory API varies by Catalyst Center version. Some versions return a per-device list in the advisory response; others return only `deviceCount` as an aggregate. If per-device detail is not in the advisory response, join with the device inventory to build the mapping based on `softwareVersion` matching.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") earliest=-7d
| head 1
| spath
| fieldsummary
| search field="*device*"
```
This shows what device-related fields are available in the advisory events.

### Step 2 — Create the search and report
If per-device data is in the advisory response:
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats latest(advisoryTitle) as title latest(severity) as sev by advisoryId, deviceId
| lookup catalyst_device_lookup deviceId OUTPUT deviceName, platformId, softwareVersion
| table advisoryId, sev, title, deviceName, platformId, softwareVersion
| sort sev, advisoryId, deviceName
```

If only `deviceCount` is available (no per-device list):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats latest(advisoryTitle) as title latest(deviceCount) as affected latest(fixedVersions) as fixes latest(cveId) as cve by advisoryId, severity
| where affected > 0
| sort case(severity="CRITICAL",1,1==1,2) -affected
```
This shows per-advisory affected counts. To get the actual device list, cross-reference with the device inventory filtered to affected firmware versions.

Why `by advisoryId, deviceId`: creates one row per advisory-device pair — the unit of remediation work. Each row says 'this specific device needs this specific patch.'

Why include `softwareVersion` from the device lookup: shows the CURRENT firmware version. The security team can see whether the device is close to the fixed version (minor upgrade, low risk) or far behind (major upgrade, more testing needed).

For most-exposed devices (which devices have the most advisory exposure):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats dc(advisoryId) as advisory_count values(advisoryId) as advisories by deviceId
| lookup catalyst_device_lookup deviceId OUTPUT deviceName, platformId, softwareVersion
| sort -advisory_count
| head 20
```
Devices with multiple CRITICAL/HIGH advisories are the highest-priority upgrade targets — one firmware push remediates multiple vulnerabilities.

Schedule: weekly (cron `0 7 * * 1`), output as CSV for the firmware upgrade team's SWIM distribution plan.

### Step 3 — Validate
(a) Pick a CRITICAL advisory from the results. Open **Catalyst Center > Security Advisories > [advisory] > Affected Devices**. Compare the device list with Splunk.

(b) Verify `softwareVersion` is current by spot-checking a device: SSH to the device, `show version`, compare with the Splunk value.

(c) Confirm the `catalyst_device_lookup` is up to date: `| inputlookup catalyst_device_lookup | stats count`. If empty, build it from the device inventory.

(d) For the most-exposed-devices variant: the top device should have the most advisory exposure. Verify in Catalyst Center that this device genuinely runs firmware affected by multiple advisories.

(e) Vendor UI parity: compare the per-advisory device list with **Catalyst Center > Security Advisories > [advisory]**.

### Step 4 — Operationalize
- Export the advisory-device table as CSV for the firmware upgrade team's SWIM distribution plan.
- Group affected devices by `platformId` — same device family = same upgrade image. This simplifies SWIM task creation.
- Prioritise: internet-facing devices first (use a `device_exposure` lookup), then CDE-scoped devices (PCI), then internal devices.
- Track per-advisory remediation progress with UC-5.13.38 (declining device count over time).

Runbook (owner: Firmware Management):
1. Receive the weekly affected-device report. Focus on CRITICAL advisories.
2. For each advisory: check if a fixed firmware version is available (from UC-5.13.34's `fixedVersions`).
3. Group affected devices by `platformId`. For each platform family: verify the fixed image is in the SWIM image repository.
4. Create a SWIM distribution task in **Catalyst Center > SWIM > Distribute Image** targeting the affected devices.
5. Schedule the upgrade during the next maintenance window. For CRITICAL with active exploitation: request emergency change window.
6. After upgrade: verify devices disappear from the affected-device list in the next poll cycle.

### Step 5 — Troubleshooting

- **`deviceId` instead of `deviceName` in results** — the `catalyst_device_lookup` is empty. Regenerate: `index=catalyst sourcetype="cisco:dnac:device" | stats latest(hostname) as deviceName latest(platformId) latest(softwareVersion) by id | rename id as deviceId | outputlookup catalyst_device_lookup`.

- **Advisory shows affected devices in Catalyst Center but 0 in Splunk** — the advisory-device mapping may be in a nested array that needs `spath | mvexpand`. Check `| head 1 | spath` for the response structure.

- **Same device appears for many advisories** — the device is running old firmware affected by multiple PSIRTs. A single firmware upgrade to a fixed version may remediate 5–10 advisories simultaneously — this is the most efficient use of upgrade effort.

- **`softwareVersion` is null in the lookup** — the device inventory input (`cisco:dnac:device`) may not be enabled. Enable it per UC-5.13.55.

- **More devices in Splunk than Catalyst Center shows** — time window difference. Narrow the Splunk search to `earliest=-2h` for the current snapshot.

- **Lookup is stale** — schedule the `outputlookup` search daily to keep device metadata current.

- **Want to see MEDIUM advisories too** — remove the severity filter. Expect a much larger result set. Use for comprehensive quarterly vulnerability reports.

- **Advisory-device mapping not in the API response** — some TA versions extract only aggregate `deviceCount`, not per-device detail. In this case, build the device list by matching `softwareVersion` against the advisory's affected versions.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats latest(advisoryTitle) as title latest(severity) as sev by advisoryId, deviceId
| lookup catalyst_device_lookup deviceId OUTPUT deviceName, platformId, softwareVersion
| table advisoryId, sev, title, deviceName, platformId, softwareVersion
| sort sev, advisoryId, deviceName
```

## Visualization

(1) Table: advisoryId, severity, advisoryTitle, deviceName, platformId, softwareVersion — drilldown to Catalyst Center Device 360. (2) Count: devices affected by CRITICAL advisories (red ≥ 1). (3) Pivot: `| stats dc(advisoryId) as advisory_count by deviceName | sort -advisory_count` — most-exposed devices first.

## Known False Positives

**Same device appearing in multiple advisories inflating the affected-device count.** A device running vulnerable software may be affected by multiple PSIRTs simultaneously, appearing multiple times in the per-device advisory view. Distinguish by using `dc(advisoryId)` per device to understand the distinct advisory count. No suppression needed — each advisory is a separate finding.

**Lab or non-production device affected by critical advisories.** Lab devices running intentionally outdated firmware may be affected by many advisories that do not warrant operational urgency. Distinguish by checking whether the device is in a non-production `siteId`. Suppress by filtering lab devices from the operational advisory dashboard using a `catalyst_excluded_devices` lookup.

**Device UUID change after RMA making the same physical device appear as a new affected device.** After RMA replacement, the new device has a different `deviceId` but the same `hostname`. The advisory may show both the old and new UUIDs as affected. Distinguish by checking whether `hostname` matches between old and new `deviceId` values. Suppress by correlating with inventory data to deduplicate by `hostname`.

**Advisory scan incomplete for large inventories.** In environments with thousands of devices, the PSIRT scan may not complete within a single poll cycle, showing an incomplete list of affected devices. Distinguish by checking whether `dc(deviceId)` increases between consecutive polls for the same `advisoryId`. Suppress by waiting for the count to stabilize (2-3 poll cycles) before using the affected-device list for operational decisions.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
