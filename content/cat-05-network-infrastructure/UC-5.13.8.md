---
id: "5.13.8"
title: "Device Uptime and Reboot Tracking"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.8 · Device Uptime and Reboot Tracking

## Description

Tracks device uptime and detects recent reboots that may indicate instability, crashlooping, or unauthorized maintenance.

## Value

Unexpected reboots are early indicators of hardware failure, software bugs, or unauthorized changes. Tracking uptime across the fleet surfaces patterns.

## Implementation

After UC-5.13.1 is online, ensure `upTime` and `lastUpdated` are extracted from the device health feed. Run this on a short lookback (for example 24h) to catch flapping platforms; add allowlists for planned maintenance. Pair with change tickets when `uptime_days` is very low but authorized.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
After UC-5.13.1 is online, ensure `upTime` and `lastUpdated` are extracted from the device health feed. Run this on a short lookback (for example 24h) to catch flapping platforms; add allowlists for planned maintenance. Pair with change tickets when `uptime_days` is very low but authorized.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(upTime) as uptime latest(lastUpdated) as last_seen by deviceName, managementIpAddress, deviceType, platformId | eval uptime_days=if(isnotnull(uptime), round(uptime/86400,1), "N/A") | where uptime_days < 1 OR uptime_days="N/A" | sort uptime_days
```

Understanding this SPL

**Device Uptime and Reboot Tracking** — Unexpected reboots are early indicators of hardware failure, software bugs, or unauthorized changes. Tracking uptime across the fleet surfaces patterns.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:devicehealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• `stats` collapses the feed to the latest `upTime` and `lastUpdated` for each device identity, giving a stable per-platform snapshot for the time window selected.
• `eval` converts seconds of uptime to days, preserving a string N/A when the value is missing so data gaps are visible as risk, not zero days.
• `where` keeps only very recent uptime (sub-one-day) or unknown uptime; `sort uptime_days` surfaces the most recently restarted devices for investigation alongside UC-5.13.1 health context.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, uptime_days, platformId, management IP), alert list for N/A cases, single value count of sub-one-day uptimes.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(upTime) as uptime latest(lastUpdated) as last_seen by deviceName, managementIpAddress, deviceType, platformId | eval uptime_days=if(isnotnull(uptime), round(uptime/86400,1), "N/A") | where uptime_days < 1 OR uptime_days="N/A" | sort uptime_days
```

## Visualization

Table (device, uptime_days, platformId, management IP), alert list for N/A cases, single value count of sub-one-day uptimes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
