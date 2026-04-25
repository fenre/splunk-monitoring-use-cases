<!-- AUTO-GENERATED from UC-5.8.10.json — DO NOT EDIT -->

---
id: "5.8.10"
title: "Firmware Update Compliance and Version Tracking (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.10 · Firmware Update Compliance and Version Tracking (Meraki)

## Description

Ensures all network devices run supported firmware versions and patches.

## Value

Ensures all network devices run supported firmware versions and patches.

## Implementation

Query device API for firmware versions. Compare to recommended baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Query device API for firmware versions. Compare to recommended baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(firmware_version) as current_fw, count as device_count by device_type
| lookup recommended_firmware.csv device_type OUTPUTNEW recommended_fw
| where current_fw != recommended_fw
```

Understanding this SPL

**Firmware Update Compliance and Version Tracking (Meraki)** — Ensures all network devices run supported firmware versions and patches.

Documented **Data sources**: `sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki:api. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki:api". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_type** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where current_fw != recommended_fw` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Firmware version table by device type; compliance percentage gauge; outdated device list.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(firmware_version) as current_fw, count as device_count by device_type
| lookup recommended_firmware.csv device_type OUTPUTNEW recommended_fw
| where current_fw != recommended_fw
```

## Visualization

Firmware version table by device type; compliance percentage gauge; outdated device list.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
