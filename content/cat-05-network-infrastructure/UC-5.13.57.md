<!-- AUTO-GENERATED from UC-5.13.57.json — DO NOT EDIT -->

---
id: "5.13.57"
title: "Image Distribution and Upgrade Progress Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.57 · Image Distribution and Upgrade Progress Tracking

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Change, Operational &middot; **Wave:** Walk &middot; **Status:** Verified

*We track the progress of software updates being rolled out across your network devices — how many have been updated successfully, how many are still waiting, and how many failed. This lets your team see at a glance whether an update campaign is on track or if some devices need manual attention.*

---

## Description

Tracks the progress of firmware distribution and upgrade operations across the managed device fleet — showing how many devices have succeeded, how many are in progress, how many are scheduled, and how many have failed — giving the firmware management team real-time visibility into upgrade campaign execution.

## Value

A firmware campaign targeting 500 devices needs a progress tracker. Without this UC, the firmware engineer refreshes the Catalyst Center SWIM UI manually to check how many succeeded. With it, the entire team — engineering, management, change advisory — can see the real-time progress in a Splunk dashboard. A campaign that's 80% SUCCESS and 15% FAILED after 24 hours has a problem that needs immediate triage. The FAILED devices need root-cause analysis (incompatible hardware, insufficient flash, network timeout) before the next maintenance window closes. For NIST CM-2, the SUCCESS count is the evidence that the baseline image was deployed. For SI-2, the FAILED count is the remediation backlog.

## Implementation

Same custom scripted input as UC-5.13.56. Filter to `upgradeStatus=*` for devices with active or completed upgrade tasks. Schedule every 30 minutes during upgrade campaigns, daily during steady state.

## Detailed Implementation

### Prerequisites
- UC-5.13.56 (Firmware Non-Compliance) must be operational — same SWIM data feed.
- The `upgradeStatus` field must be populated by the scripted input. Not all SWIM API endpoints return upgrade status — verify with `| fieldsummary | search field=upgradeStatus`.
- This UC is most useful during active firmware campaigns. Configure a higher poll frequency (every 30 minutes) during campaign windows and daily polling during steady state.

### Step 1 — Configure data collection
Same custom scripted input as UC-5.13.56. During active campaigns, consider reducing the poll interval from 3600s to 1800s for faster progress visibility.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=* earliest=-24h
| stats count by upgradeStatus
```
If no results, the `upgradeStatus` field may not be in the API response. Check the scripted input output format.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=*
| stats count as devices by upgradeStatus, deviceFamily
| eval status_order=case(upgradeStatus="FAILED",1, upgradeStatus="IN_PROGRESS",2, upgradeStatus="SCHEDULED",3, upgradeStatus="SUCCESS",4, 1==1,5)
| sort status_order -devices
```

Why sort FAILED first: the most operationally urgent information is the failure count. FAILED devices need immediate triage — the firmware engineer should see them at the top of the table.

Why `by deviceFamily`: different platform families may have different success rates (e.g., all 9300s succeeded but 9500s failed due to a different image requirement). The per-family breakdown directs troubleshooting to the right platform team.

For a campaign progress dashboard during active upgrades:
```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=*
| stats dc(deviceName) as total dc(eval(if(upgradeStatus="SUCCESS",deviceName,null()))) as succeeded dc(eval(if(upgradeStatus="FAILED",deviceName,null()))) as failed dc(eval(if(upgradeStatus="IN_PROGRESS",deviceName,null()))) as in_progress
| eval pct_complete=round(succeeded*100/total,1)
```

For FAILED device detail (triage list):
```spl
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus="FAILED"
| stats latest(runningVersion) as running latest(targetVersion) as target by deviceName, deviceFamily, managementIpAddress
| table deviceName, managementIpAddress, deviceFamily, running, target
```

Schedule: every 30 minutes during campaigns, daily otherwise.

### Step 3 — Validate
(a) During an active SWIM distribution, compare the SUCCESS/FAILED/IN_PROGRESS counts with **Catalyst Center > SWIM > Distribution Task > [task detail]**.
(b) Pick a FAILED device and verify the failure in Catalyst Center's SWIM task detail.
(c) After a campaign completes, verify all SUCCESS devices show as COMPLIANT in UC-5.13.56.
(d) Vendor UI parity: compare progress percentages with the SWIM task progress bar in Catalyst Center.

### Step 4 — Operationalize
- Campaign war-room dashboard: progress gauge + FAILED device list, refreshing every 30 minutes.
- Post-campaign report: SUCCESS/FAILED/IN_PROGRESS summary for the change record.
- NIST CM-2 evidence: SUCCESS count demonstrates baseline deployment. FAILED count with root-cause analysis demonstrates remediation effort.

Runbook (owner: Firmware Management, during active campaigns):
1. Monitor the progress gauge every 30 minutes during the maintenance window.
2. If SUCCESS rate plateaus: check whether remaining devices are IN_PROGRESS (still upgrading) or FAILED (need investigation).
3. For FAILED devices: check the failure reason in Catalyst Center SWIM task detail. Common causes:
   - Insufficient flash → hardware refresh required.
   - Network timeout → retry during the next window.
   - Incompatible platform → wrong image selected for this device family.
   - Device unreachable → check UC-5.13.6 (Reachability).
4. For devices stuck IN_PROGRESS > 2 hours: the upgrade may be hung. Check device console for boot loop or crash.
5. Post-campaign: generate the final SUCCESS/FAILED report and attach to the change ticket.

### Step 5 — Troubleshooting

- **`upgradeStatus` field is null** — the scripted input may not extract this field. Check `| head 1 | spath` for available fields. The SWIM API response structure varies between Catalyst Center versions.

- **All devices show SCHEDULED but none transition to IN_PROGRESS** — the SWIM distribution task may not have started. Check the task schedule in **Catalyst Center > SWIM > Scheduled Tasks**.

- **FAILED count is very high** — systematic issue. Check whether the golden image is valid for the target platform. A mismatched image (e.g., switch image for a router) will fail every device.

- **SUCCESS count doesn't match UC-5.13.56 COMPLIANT count** — some SUCCESS devices may have reverted to the old image on reboot. Check boot variable configuration.

- **Progress gauge doesn't update** — the poll interval may be too long (3600s). Reduce to 1800s during campaigns.

- **Want to track multiple concurrent campaigns** — add a `taskId` or `campaignId` field to the scripted input to distinguish between campaigns.

- **Upgrade velocity is slower than expected** — Catalyst Center SWIM distributes images serially within each task. Large device populations may need multiple parallel tasks.

- **Devices show IN_PROGRESS for > 6 hours** — likely hung. Check the device console for crash loops or boot failures. May need manual intervention.

Additional operational context for Image Distribution and Upgrade Progress Tracking:

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
index=catalyst sourcetype="cisco:dnac:swim" upgradeStatus=*
| stats count as devices by upgradeStatus, deviceFamily
| eval status_order=case(upgradeStatus="FAILED",1, upgradeStatus="IN_PROGRESS",2, upgradeStatus="SCHEDULED",3, upgradeStatus="SUCCESS",4, 1==1,5)
| sort status_order -devices
```

## Visualization

(1) Stacked bar: device count by upgradeStatus (SUCCESS green, IN_PROGRESS blue, SCHEDULED grey, FAILED red) × deviceFamily. (2) Progress gauge: % SUCCESS out of total. (3) Table: FAILED devices with deviceName, deviceFamily, runningVersion, targetVersion. (4) Timechart: `| timechart span=1h count by upgradeStatus` during an active campaign.

## Known False Positives

**IN_PROGRESS devices during active maintenance window.** Devices currently being upgraded show IN_PROGRESS — this is expected during the maintenance window. Distinguish by checking whether the maintenance window is active. Only investigate IN_PROGRESS devices that persist > 4 hours past the maintenance window end.

**SCHEDULED devices before the maintenance window.** Devices queued for upgrade show SCHEDULED before the window opens. This is not a problem — they'll transition to IN_PROGRESS when the upgrade begins.

**FAILED devices due to insufficient flash storage.** Older devices may lack flash capacity for the golden image. Distinguish by checking the failure reason in the SWIM task detail. These require hardware refresh, not a retry.

**SUCCESS devices reverting to NON_COMPLIANT after reboot.** Some devices reload into the old image if the boot variable isn't set correctly. Distinguish by checking UC-5.13.56 (Firmware Non-Compliance) after the upgrade window — devices that show SUCCESS but are still NON_COMPLIANT have a boot configuration issue.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center SWIM — Image Distribution](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/swim-guide.html)
- [Catalyst Center Integration Guide — Custom Scripted Inputs](docs/guides/catalyst-center.md#custom-scripted-inputs)
- [NIST SP 800-53 Rev. 5 — CM-2 Baseline Configuration](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-2)
