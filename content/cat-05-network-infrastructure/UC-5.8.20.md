<!-- AUTO-GENERATED from UC-5.8.20.json — DO NOT EDIT -->

---
id: "5.8.20"
title: "Configuration Change Window Compliance (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.20 · Configuration Change Window Compliance (Meraki)

## Description

Ensures configuration changes only occur within approved maintenance windows.

## Value

Ensures configuration changes only occur within approved maintenance windows.

## Implementation

Monitor configuration change events. Check against maintenance windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event signature="*config*"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor configuration change events. Check against maintenance windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*config*"
| eval hour=strftime(_time, "%H")
| stats count as config_change_count by hour
| eval window_compliant=if(hour>=22 OR hour<6, "Yes", "No")
| where window_compliant="No" AND config_change_count > 0
```

Understanding this SPL

**Configuration Change Window Compliance (Meraki)** — Ensures configuration changes only occur within approved maintenance windows.

Documented **Data sources**: `sourcetype=meraki type=security_event signature="*config*"`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **hour** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by hour** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **window_compliant** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where window_compliant="No" AND config_change_count > 0` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In Meraki Dashboard, open the same organization or network, compare the metric (status, event feed, or admin log) to the Splunk result, and confirm the TA’s API key, org ID, and optional syslog reach the same index and sourcetype you used in the search.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Change compliance timeline; out-of-window change alert table.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*config*"
| eval hour=strftime(_time, "%H")
| stats count as config_change_count by hour
| eval window_compliant=if(hour>=22 OR hour<6, "Yes", "No")
| where window_compliant="No" AND config_change_count > 0
```

## Visualization

Change compliance timeline; out-of-window change alert table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
