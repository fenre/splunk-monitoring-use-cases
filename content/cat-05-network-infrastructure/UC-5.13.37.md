---
id: "5.13.37"
title: "Devices Affected by Active Advisories"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.37 · Devices Affected by Active Advisories

## Description

Maps security advisories to specific devices, showing which devices have the most advisories and which have critical-severity vulnerabilities.

## Value

Knowing which devices are most exposed enables risk-based patching prioritization — fix the devices with the most critical advisories first.

## Implementation

Enable the `securityadvisory` input. If `searchmatch` is noisy on multivalue `severities`, consider `mvfind` or `where mvfilter` patterns instead after validating the field format.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:securityadvisory (deviceId, deviceName, platformId, advisoryId, severity).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `securityadvisory` input. If `searchmatch` is noisy on multivalue `severities`, consider `mvfind` or `where mvfilter` patterns instead after validating the field format.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count values(advisoryId) as advisories values(severity) as severities by deviceId, deviceName, platformId | eval has_critical=if(searchmatch("*CRITICAL*"),1,0) | sort -has_critical -advisory_count
```

Understanding this SPL

**Devices Affected by Active Advisories** — Knowing which devices are most exposed enables risk-based patching prioritization — fix the devices with the most critical advisories first.

**Pipeline walkthrough**

• Groups advisory activity per device (`deviceId`, `deviceName`, `platformId`) and counts how many records exist, listing related advisories and severities for quick inspection.
• `searchmatch` on the concatenated severities is a quick signal for the presence of critical strings; refine if your events use a strict `severity` field instead of multivalue text.
• Sorting by `has_critical` then `advisory_count` brings the most dangerous and noisiest assets to the top.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (advisory_count, severities, advisories by device), bar chart of top at-risk deviceId.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats count as advisory_count values(advisoryId) as advisories values(severity) as severities by deviceId, deviceName, platformId | eval has_critical=if(searchmatch("*CRITICAL*"),1,0) | sort -has_critical -advisory_count
```

## Visualization

Table (advisory_count, severities, advisories by device), bar chart of top at-risk deviceId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
