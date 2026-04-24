---
id: "5.13.26"
title: "Issue Distribution by Device and Site"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.26 · Issue Distribution by Device and Site

## Description

Maps assurance issues to specific devices and sites to identify problem hotspots in the network infrastructure.

## Value

Some devices or sites generate disproportionate issue volumes. Identifying these hotspots focuses remediation where it has the most impact.

## Implementation

Enable the `issue` input. Confirm `siteId` is extracted from Catalyst Center issue payloads. If the field is missing, enrich using a site lookup or device inventory from Catalyst Center inventory feeds in Splunk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:issue (fields deviceId, siteId, name).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `issue` input. Confirm `siteId` is extracted from Catalyst Center issue payloads. If the field is missing, enrich using a site lookup or device inventory from Catalyst Center inventory feeds in Splunk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as issue_count dc(name) as unique_issues by deviceId, siteId | sort -issue_count | head 20
```

Understanding this SPL

**Issue Distribution by Device and Site** — Some devices or sites generate disproportionate issue volumes. Identifying these hotspots focuses remediation where it has the most impact.

**Pipeline walkthrough**

• Groups issue events by `deviceId` and `siteId` to create a per-location workload view.
• `stats` counts all issues and counts distinct `name` values to show breadth versus repetition at each site or device.
• `sort` and `head 20` surface the noisiest locations for targeted engineering follow-up.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (top 20 by issue_count), treemap or packed bubble by siteId and deviceId.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | stats count as issue_count dc(name) as unique_issues by deviceId, siteId | sort -issue_count | head 20
```

## Visualization

Table (top 20 by issue_count), treemap or packed bubble by siteId and deviceId.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
