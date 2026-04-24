---
id: "5.13.35"
title: "Critical/High PSIRT Alerting"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.35 · Critical/High PSIRT Alerting

## Description

Alerts on critical and high severity PSIRTs affecting managed devices, with the count of affected devices and associated CVEs.

## Value

Critical and high PSIRTs require immediate remediation. Alerting with affected device counts helps prioritize patching based on blast radius.

## Implementation

Enable the `securityadvisory` input. Use as a scheduled alert with low latency for CRITICAL, and include advisoryTitle and cves in the payload for analysts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:securityadvisory (severity, deviceId, cveId, advisoryId, advisoryTitle).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `securityadvisory` input. Use as a scheduled alert with low latency for CRITICAL, and include advisoryTitle and cves in the payload for analysts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") | stats dc(deviceId) as affected_devices values(cveId) as cves latest(advisoryId) as advisory by severity, advisoryTitle | sort severity -affected_devices
```

Understanding this SPL

**Critical/High PSIRT Alerting** — Critical and high PSIRTs require immediate remediation. Alerting with affected device counts helps prioritize patching based on blast radius.

**Pipeline walkthrough**

• Filters the advisory stream down to the two most severe `severity` levels.
• `stats` measures distinct impacted `deviceId` values, collects related `cveId` values, and keeps the most recent `advisoryId` per `severity` and `advisoryTitle` group.
• `sort` orders by `severity` then descending `affected_devices` to emphasise the largest exposures.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table (affected_devices, cves, advisory by severity and title), top-N list for P1 remediation.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") | stats dc(deviceId) as affected_devices values(cveId) as cves latest(advisoryId) as advisory by severity, advisoryTitle | sort severity -affected_devices
```

## Visualization

Table (affected_devices, cves, advisory by severity and title), top-N list for P1 remediation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
