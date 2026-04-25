<!-- AUTO-GENERATED from UC-5.13.54.json — DO NOT EDIT -->

---
id: "5.13.54"
title: "Site-to-Device Ratio and Capacity Planning"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.54 · Site-to-Device Ratio and Capacity Planning

## Description

Analyzes the distribution of devices across sites to identify over-provisioned or under-provisioned locations for capacity planning.

## Value

Understanding device density per site helps plan hardware refreshes, license allocation, and support staffing across locations.

## Implementation

Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls site hierarchy data from the Catalyst Center Intent API every 60 minutes. Key fields: `siteId`, `siteType` (area, building, floor), `parentSiteName`, `siteName`, `deviceId` when present in the event payload.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on for Splunk (7538) with **site topology** in `index=catalyst`, sourcetype `cisco:dnac:site:topology` (Intent API site topology, including device-to-site when your TA version emits `deviceId`).
• Service account: **`SUPER-ADMIN-ROLE`** or **`NETWORK-ADMIN-ROLE`** (or equivalent) so the TA can read topology and device membership; limited roles may return partial sites.
• `docs/implementation-guide.md` for where inputs run and how to set the destination index.

Step 1 — Configure data collection
• **TA input:** `site_topology` (name may vary by release); default interval is often **3600 seconds (1 hour)** for hierarchy.
• **Key fields:** `siteId`, `siteName`, `siteType`, and `deviceId` when the payload includes it; if `deviceId` is missing, extend collection or join to **device** inventory in a follow-on UC — without `deviceId`, this search cannot count per site.

Step 2 — Create the report

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as device_count by siteId, siteName, siteType | eventstats avg(device_count) as avg_devices_per_site stdev(device_count) as stdev_devices | eval density_score=round((device_count-avg_devices_per_site)/if(stdev_devices>0,stdev_devices,1),1) | sort -device_count
```

Understanding this SPL
• **Density score** is a z-style distance from the fleet mean; it highlights statistical outliers, not “bad” by itself — interpret next to your campus reference design.
• When `stdev_devices` is 0, the `if()` guard uses 1 to avoid divide-by-zero; all identical counts yield density_score near zero even if a site is large in absolute terms.

**Pipeline walkthrough**
• `dc(deviceId)` by site dimensions; `eventstats` across the result set; `sort -device_count` lists the largest sites first for capacity follow-up.

Step 3 — Validate
• Spot-check a large and a small site against **Catalyst Center** device counts per site; note topology poll lag (up to an hour) versus live UI.

Step 4 — Operationalize
• Use as a **monthly** capacity readout; pair with `siteName` and building owner for planning meetings.

Step 5 — Troubleshooting
• **Blank or null `deviceId`:** verify the TA and Catalyst Center version actually ship device mapping in the topology event; you may need a **join** to `cisco:dnac:device` inventory from another input.
• **Wild swings after upgrades:** new site types or reparenting can re-bucket `deviceId` into different `siteId` rows; re-run after two poll cycles and compare to the **Sites** UI.
• **Outlier noise:** if only a few very large sites exist, prefer fixed thresholds (for example by `siteType=floor` only) instead of only z-score for alerting.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as device_count by siteId, siteName, siteType | eventstats avg(device_count) as avg_devices_per_site stdev(device_count) as stdev_devices | eval density_score=round((device_count-avg_devices_per_site)/if(stdev_devices>0,stdev_devices,1),1) | sort -device_count
```

## Visualization

Table (siteName, siteType, device_count, density_score), bar chart of device_count, scatter of density_score versus siteType.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
