<!-- AUTO-GENERATED from UC-5.13.8.json — DO NOT EDIT -->

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
• Cisco Catalyst Add-on for Splunk (Splunkbase 7538) with **devicehealth** writing `cisco:dnac:devicehealth` to `index=catalyst`.
• Complete **UC-5.13.1** so device identity fields are trustworthy; confirm **`upTime`** and **`lastUpdated`** appear in raw device-health JSON (names can vary slightly by Catalyst Center release—spot-check one event).
• Catalyst Center **2.3.5+** with Assurance device health; service account with **`NETWORK-ADMIN-ROLE`** or **`SUPER-ADMIN-ROLE`**.
• See `docs/implementation-guide.md` for credential storage and input enablement.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/device-health` (same feed as other device-health UCs).
• **TA input:** **devicehealth** modular input; sourcetype `cisco:dnac:devicehealth`; default poll **900 seconds**.
• **Fields:** `upTime` is typically in seconds since last boot; `lastUpdated` marks freshness of the health record.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(upTime) as uptime latest(lastUpdated) as last_seen by deviceName, managementIpAddress, deviceType, platformId | eval uptime_days=if(isnotnull(uptime), round(uptime/86400,1), "N/A") | where uptime_days < 1 OR uptime_days="N/A" | sort uptime_days
```

Understanding this SPL
• **Sub-one-day uptime** flags very recent restarts; tune **`< 1`** to **0.5** days or add **exclusion** lookups for change windows if noise persists.
• **`N/A` uptime** is kept visible—treat as “unknown” in triage, not a guaranteed reboot.
• Add **`siteId`** to the `by` clause if you need location-scoped review lists.

**Pipeline walkthrough**
• `latest(upTime)` and `latest(lastUpdated)` per device give one row per key for the search window.
• `eval` converts seconds to **days** with a string **N/A** when missing.
• `where` + `sort` list the freshest restarts and unknowns first for correlation with **UC-5.13.1** health and **UC-5.13.3** reachability.

Step 3 — Validate (parity with Catalyst Center and field sanity)
• In Search, `| fieldsummary upTime` on `cisco:dnac:devicehealth` to confirm numeric type and value range.
• Pick a device you reloaded in a window: compare **upTime** in Splunk to **Device 360** / CLI **show version** uptime for the same period (allow one poll skew).
• If **all** rows are **N/A**, the TA or props may not be extracting `upTime`—fix before alerting.

Step 4 — Operationalize
• **Dashboard:** table on a **stability** row beside device health; filter **24h** for “recently restarted” reviews.
• **Alerting (optional):** schedule on a **15–60 minute** cadence; **throttle** per **deviceName**; attach **change ticket** number in the runbook for expected reloads.
• **Runbook:** link to **Catalyst Center** device and to **show crashinfo** / **show logging** on the device when uptime is short without a matching change.

Step 5 — Troubleshooting
• **No `upTime` in events:** confirm **Assurance** and inventory sync; re-check raw JSON and **props.conf** for the sourcetype.
• **False surge after TA upgrade:** field rename or double-ingest—validate with `| dedup _time, deviceName` in a test.
• **Windows-only playbooks in your org:** this UC is for **Catalyst** network devices; ignore unrelated host-reboot content if copied from other templates.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" | stats latest(upTime) as uptime latest(lastUpdated) as last_seen by deviceName, managementIpAddress, deviceType, platformId | eval uptime_days=if(isnotnull(uptime), round(uptime/86400,1), "N/A") | where uptime_days < 1 OR uptime_days="N/A" | sort uptime_days
```

## Visualization

Table (device, uptime_days, platformId, management IP), alert list for N/A cases, single value count of sub-one-day uptimes.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
