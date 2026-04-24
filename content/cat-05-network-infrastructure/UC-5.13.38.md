---
id: "5.13.38"
title: "Advisory Remediation Progress Tracking"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.38 · Advisory Remediation Progress Tracking

## Description

Tracks the remediation progress of security advisories over time by comparing current affected device counts against historical baselines.

## Value

Vulnerability remediation is a process, not a one-time event. Tracking progress demonstrates active management and identifies stalled remediation efforts.

## Implementation

Enable the `securityadvisory` input. `appendcols` requires aligned `advisoryId` order between the two `stats` outputs; for production, consider a `join` on `advisoryId` or `lookup` of precomputed baselines. Validate that subsearch time bounds cover representative weeks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:securityadvisory (advisoryId, severity, deviceId, advisoryTitle; compare windows with earliest/latest).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `securityadvisory` input. `appendcols` requires aligned `advisoryId` order between the two `stats` outputs; for production, consider a `join` on `advisoryId` or `lookup` of precomputed baselines. Validate that subsearch time bounds cover representative weeks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(deviceId) as current_affected by advisoryId, severity, advisoryTitle | appendcols [search index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-30d latest=-7d | stats dc(deviceId) as previous_affected by advisoryId] | eval remediation_pct=if(previous_affected>0, round((previous_affected-current_affected)*100/previous_affected,1), "N/A") | where current_affected > 0 | sort severity -current_affected
```

Understanding this SPL

**Advisory Remediation Progress Tracking** — Vulnerability remediation is a process, not a one-time event. Tracking progress demonstrates active management and identifies stalled remediation efforts.

**Pipeline walkthrough**

• The main `stats` builds current exposure per advisory using distinct `deviceId` counts in the user-selected (typically recent) window.
• The subsearch repeats the count for a historical slice (`earliest=-30d latest=-7d`) as a simple baseline of previous blast radius by `advisoryId`.
• `remediation_pct` approximates the percentage drop in affected devices; `where current_affected > 0` keeps only still-relevant work items.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (advisoryId, severity, current_affected, previous_affected, remediation_pct), column chart of remediation_pct.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats dc(deviceId) as current_affected by advisoryId, severity, advisoryTitle | appendcols [search index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-30d latest=-7d | stats dc(deviceId) as previous_affected by advisoryId] | eval remediation_pct=if(previous_affected>0, round((previous_affected-current_affected)*100/previous_affected,1), "N/A") | where current_affected > 0 | sort severity -current_affected
```

## Visualization

Table (advisoryId, severity, current_affected, previous_affected, remediation_pct), column chart of remediation_pct.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
