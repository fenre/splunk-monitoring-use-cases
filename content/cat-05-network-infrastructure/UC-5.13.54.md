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
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:site:topology (Catalyst Center site; fields siteId, siteName, siteType, deviceId).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `site_topology` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls site hierarchy data from the Catalyst Center Intent API every 60 minutes. Key fields: `siteId`, `siteType` (area, building, floor), `parentSiteName`, `siteName`, `deviceId` when present in the event payload.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as device_count by siteId, siteName, siteType | eventstats avg(device_count) as avg_devices_per_site stdev(device_count) as stdev_devices | eval density_score=round((device_count-avg_devices_per_site)/if(stdev_devices>0,stdev_devices,1),1) | sort -device_count
```

Understanding this SPL

**Site-to-Device Ratio and Capacity Planning** — Understanding device density per site helps plan hardware refreshes, license allocation, and support staffing across locations.

**Pipeline walkthrough**

• Counts `dc(deviceId)` for each `siteId`, `siteName`, and `siteType` triplet to measure site population.
• `eventstats` computes the average and standard deviation of `device_count` across the current result set to describe fleet central tendency and spread.
• `eval` yields a `density_score` in standard-deviation units from the mean, guarding divide-by-zero when all sites are identical. Higher absolute scores highlight outliers.
• `sort -device_count` still ranks by raw size for the biggest sites, while the score column shows statistical outliers.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (siteName, siteType, device_count, density_score), bar chart of device_count, scatter of density_score versus siteType.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:site:topology" | stats dc(deviceId) as device_count by siteId, siteName, siteType | eventstats avg(device_count) as avg_devices_per_site stdev(device_count) as stdev_devices | eval density_score=round((device_count-avg_devices_per_site)/if(stdev_devices>0,stdev_devices,1),1) | sort -device_count
```

## Visualization

Table (siteName, siteType, device_count, density_score), bar chart of device_count, scatter of density_score versus siteType.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
