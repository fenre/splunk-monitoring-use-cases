---
id: "5.13.36"
title: "Advisory Trending and New Advisory Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.36 · Advisory Trending and New Advisory Detection

## Description

Identifies newly detected security advisories in the last 7 days, enabling rapid assessment of new vulnerabilities affecting the managed network.

## Value

New advisories require immediate triage. Detecting them as soon as Catalyst Center reports them ensures the vulnerability management process starts promptly.

## Implementation

Enable the `securityadvisory` input. The `where first_seen` window compares the earliest event per advisory to `now()`. Adjust the `-7d` lookback to match your patch SLAs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:securityadvisory (advisoryId, advisoryTitle, severity, deviceId, _time).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the `securityadvisory` input. The `where first_seen` window compares the earliest event per advisory to `now()`. Adjust the `-7d` lookback to match your patch SLAs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats earliest(_time) as first_seen latest(_time) as last_seen dc(deviceId) as affected_devices by advisoryId, advisoryTitle, severity | eval first_seen_date=strftime(first_seen, "%Y-%m-%d") | where first_seen > relative_time(now(), "-7d") | sort severity -affected_devices
```

Understanding this SPL

**Advisory Trending and New Advisory Detection** — New advisories require immediate triage. Detecting them as soon as Catalyst Center reports them ensures the vulnerability management process starts promptly.

**Pipeline walkthrough**

• `stats` summarises one row per `advisoryId` / `advisoryTitle` / `severity`, capturing the first/last time that advisory was seen in the data and how many `deviceId` values are touched.
• `first_seen_date` is a human-friendly display field for reports.
• `where first_seen` keeps advisories that first arrived within the last seven days so the search highlights fresh risk.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Consider visualizations: Table of new advisories (first_seen_date, affected_devices), timechart of first_seen counts.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats earliest(_time) as first_seen latest(_time) as last_seen dc(deviceId) as affected_devices by advisoryId, advisoryTitle, severity | eval first_seen_date=strftime(first_seen, "%Y-%m-%d") | where first_seen > relative_time(now(), "-7d") | sort severity -affected_devices
```

## Visualization

Table of new advisories (first_seen_date, affected_devices), timechart of first_seen counts.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
