<!-- AUTO-GENERATED from UC-5.13.58.json — DO NOT EDIT -->

---
id: "5.13.58"
title: "SWIM Upgrade Failure Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.58 · SWIM Upgrade Failure Alerting

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability, Change &middot; **Wave:** Walk &middot; **Status:** Verified

*We set up an alarm that goes off when a software update fails on any network device. During an update window, failures need to be caught quickly so the team can fix the problem before the maintenance window closes — otherwise that device stays on the old software until next month.*

---

## Description

Fires an alert when any firmware upgrade operation fails, providing the failed device name, IP, current and target firmware versions, and the failure reason — enabling the firmware team to triage failures immediately during the maintenance window before it closes, rather than discovering them in the next day's compliance report.

## Value

A failed firmware upgrade during a maintenance window is a time-critical event. The window is typically 4–8 hours, and every failed device needs triage before the window closes — because once the window ends, the device is stuck on the old firmware until the next window. The `failureReason` field tells the engineer whether to retry (network timeout), escalate (incompatible platform), or plan hardware refresh (insufficient flash). Without this alert, the engineer checks SWIM manually at the end of the window and may miss failures that need investigation. For NIST IR-4, the alert-to-ticket pipeline demonstrates incident handling for failed infrastructure changes.

## Implementation

Same custom scripted input as UC-5.13.56. Filter to `upgradeStatus="FAILED"`. Schedule every 30 minutes during maintenance windows. Route to the firmware engineering team immediately.

## Detailed Implementation

### Prerequisites
- UC-5.13.56 (Firmware Non-Compliance) and UC-5.13.57 (Upgrade Progress) must be operational — same SWIM data feed.
- The `upgradeStatus` and `failureReason` fields must be present in the scripted input output. Not all SWIM API endpoints return failure reasons — verify with `| fieldsummary | search field IN ("upgradeStatus","failureReason")`.
- This alert is most valuable during active firmware campaigns. Configure the alert schedule to match your maintenance window cadence.

### Step 1 — Configure data collection
Same custom scripted input as UC-5.13.56. During campaigns, consider polling every 30 minutes instead of hourly for faster failure detection.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED"
| stats latest(runningVersion) as running latest(targetVersion) as target latest(failureReason) as reason by deviceName, deviceFamily, managementIpAddress
| table deviceName, managementIpAddress, deviceFamily, running, target, reason
| sort deviceFamily, deviceName
```

Why `latest()` per device: if the upgrade fails multiple times across polls, `latest()` gives the most recent failure state.

Why include `failureReason`: this is the most actionable field. It tells the engineer whether to retry, escalate, or plan hardware refresh — without needing to open the Catalyst Center SWIM UI.

Why include `managementIpAddress`: allows the engineer to SSH/console to the device immediately for manual investigation.

Schedule as Alert:
- During campaigns: `*/30 * * * *` (every 30 minutes)
- Steady state: `0 7 * * *` (daily morning check)
- Trigger: "Number of results > 0"
- Throttle: by `deviceName` for `24h`

### Step 3 — Validate
(a) After a SWIM distribution task completes, compare the Splunk FAILED list with **Catalyst Center > SWIM > [task] > Failed Devices**.
(b) Verify `failureReason` contains useful diagnostic information — not just a generic `FAILED` string.
(c) Check that SUCCESS devices from the same campaign are NOT in the FAILED results (deduplication check).
(d) Vendor UI parity: compare the failed device count with SWIM task failure count in Catalyst Center.

### Step 4 — Operationalize
- Alert: page the firmware engineering team during active campaigns. Include deviceName, IP, deviceFamily, running, target, and failureReason.
- Post-campaign: generate the FAILED device report and attach to the change ticket.
- Track: how many devices fail per campaign? Is the failure rate improving?
- For NIST IR-4: document the alert → triage → remediation pipeline for each failed upgrade.

Runbook (owner: Firmware Engineering, during active campaigns):
1. Receive failure alert. Note `deviceName` and `failureReason`.
2. Triage by reason:
   - **Timeout / connection error** → retry the upgrade. Check network path between Catalyst Center and device.
   - **Insufficient flash** → device needs hardware refresh. Document and schedule replacement.
   - **Incompatible platform** → wrong image for this device family. Check golden image assignment in SWIM.
   - **Boot failure** → device may be in a crashloop. Check console access. May need manual ROMMON recovery.
   - **Unknown / generic** → check Catalyst Center SWIM task detail for more information.
3. For devices that can't be upgraded this window: document the failure and schedule for the next window.
4. After window closes: generate the final campaign report (UC-5.13.57) with SUCCESS/FAILED summary.

### Step 5 — Troubleshooting

- **`upgradeStatus="FAILED"` but no events appear** — the scripted input may not track `upgradeStatus`. Check `| stats values(upgradeStatus)` for available values.

- **`failureReason` is null** — the SWIM API may not expose failure reasons at the device level. Check Catalyst Center SWIM task detail for the reason.

- **Same device FAILED across multiple campaigns** — persistent hardware or configuration issue. Escalate to Cisco TAC.

- **All devices in a family FAILED** — wrong image selected. Check the SWIM golden image assignment.

- **FAILED count increases between polls** — more devices are being attempted and failing. Check whether the SWIM distribution task is still running.

- **Alert fires during non-campaign periods** — an ad-hoc upgrade was attempted. Verify with the change record.

- **Device shows FAILED but `show version` shows the new firmware** — the SWIM task may have reported failure but the upgrade actually succeeded. Verify with UC-5.13.56.

- **Want to track failure rate per campaign** — add a `campaign_id` or date range to the search to isolate individual campaign results.

Additional operational context for SWIM Upgrade Failure Alerting:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED"
| stats latest(runningVersion) as running latest(targetVersion) as target latest(failureReason) as reason by deviceName, deviceFamily, managementIpAddress
| table deviceName, managementIpAddress, deviceFamily, running, target, reason
| sort deviceFamily, deviceName
```

## Visualization

(1) Table: FAILED devices with deviceName, IP, deviceFamily, running, target, reason. (2) Single value: count of FAILED devices (red ≥ 1). (3) Alert payload includes all fields for immediate triage. (4) Drilldown to UC-5.13.57 for campaign-wide progress context.

## Known False Positives

**Transient network timeout causing single-attempt failure.** A temporary network issue between Catalyst Center and the device can cause the image transfer to fail. Distinguish by checking whether the failure reason contains `timeout` or `connection`. Suppress by retrying the upgrade — if it succeeds on retry, the initial failure was transient.

**Insufficient flash storage on older devices.** Older devices (Catalyst 3560, 3750) may not have enough flash for newer images. Distinguish by checking `failureReason` for `insufficient space` or `flash`. Do not suppress — this indicates the device needs hardware refresh.

**Wrong image selected for the platform.** A switch image applied to a router platform will fail with an incompatibility error. Distinguish by checking `failureReason` for `incompatible` or `platform mismatch`. Fix: correct the golden image assignment in SWIM for that device family.

**Device already running a newer version.** If a device is ahead of the golden image (e.g., emergency patch), the downgrade may fail if SWIM doesn't support downgrades. Distinguish by comparing `running` > `target`. Consider updating the golden image instead of downgrading the device.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center SWIM — Troubleshooting Image Distribution](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/swim-guide.html)
- [Catalyst Center Integration Guide — Custom Scripted Inputs](docs/guides/catalyst-center.md#custom-scripted-inputs)
- [NIST SP 800-53 Rev. 5 — IR-4 Incident Handling](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=IR-4)
