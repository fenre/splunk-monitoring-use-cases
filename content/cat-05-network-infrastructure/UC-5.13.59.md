<!-- AUTO-GENERATED from UC-5.13.59.json — DO NOT EDIT -->

---
id: "5.13.59"
title: "End-of-Life / End-of-Support Software Detection"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.59 · End-of-Life / End-of-Support Software Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Inventory &middot; **Wave:** Walk &middot; **Status:** Verified

*We find network devices running software that the manufacturer no longer supports — meaning no more security fixes will ever be made for those versions. These devices are ticking time bombs that need to be upgraded or replaced before a vulnerability is discovered that can never be patched.*

---

## Description

Identifies devices running software versions that have reached or are approaching end-of-life (EoL) or end-of-support (EoS) status — meaning Cisco no longer provides security patches, bug fixes, or TAC support — creating an unacceptable risk for production infrastructure.

## Value

EoL/EoS software is the single biggest ongoing security risk in most enterprise networks. Once a firmware version reaches End of Software Maintenance, no new security patches will be released — any vulnerability discovered after that date is permanently unpatched. This UC identifies exactly which devices are affected, when their support ended (or will end), and which firmware versions they're running, giving the asset management and network engineering teams the data they need to plan and prioritise refresh projects. For NIST SA-22 (Unsupported System Components), this is the primary detection control.

## Implementation

Requires SWIM lifecycle data from the custom scripted input. Some Catalyst Center versions expose EoL/EoS status via the compliance or lifecycle API. Configure daily polling. Schedule monthly for the asset management review.

## Detailed Implementation

### Prerequisites
- Custom scripted input for SWIM data (UC-5.13.56) must be deployed, extended to include EoL/EoS lifecycle fields.
- The Catalyst Center API must expose lifecycle/EoL data for your version. Check the Intent API reference for `eolStatus`, `eolDate` fields in the device or compliance endpoints.
- Service account with **NETWORK-ADMIN-ROLE** for lifecycle data.
- For NIST SA-22, document the organisation's policy on unsupported components: maximum time allowed on EoL software, required compensating controls, exception approval process.

### Step 1 — Configure data collection
Same custom scripted input as UC-5.13.56, extended to emit `eolStatus` and `eolDate` fields. Poll daily (86400s) — lifecycle status changes slowly.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:swim" eolStatus=* earliest=-2d
| stats dc(deviceName) as devices by eolStatus
```
If no results, the scripted input may not be extracting EoL fields. Check `| head 1 | spath` for available lifecycle fields.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:swim" (eolStatus="END_OF_LIFE" OR eolStatus="END_OF_SUPPORT" OR eolStatus="END_OF_SW_MAINTENANCE")
| stats dc(deviceName) as affected_devices values(runningVersion) as versions by deviceFamily, eolStatus, eolDate
| sort eolDate
```

Why `by deviceFamily, eolStatus, eolDate`: groups by platform family and lifecycle status, showing the EoL date for each group. Sorted by `eolDate` ascending — the most urgent (earliest EoL date) appears first.

Why `dc(deviceName)` as affected_devices: counts unique devices per lifecycle category. This is the hardware refresh backlog.

For upcoming EoL detection (devices not yet EoL but approaching):
```spl
index=catalyst sourcetype="cisco:dnac:swim" eolDate=*
| eval eol_epoch=strptime(eolDate, "%Y-%m-%d")
| eval days_to_eol=round((eol_epoch-now())/86400,0)
| where days_to_eol > 0 AND days_to_eol < 180
| stats dc(deviceName) as devices by deviceFamily, eolDate, eolStatus
| eval urgency=case(days_to_eol<30,"CRITICAL", days_to_eol<90,"HIGH", 1==1,"PLAN")
| sort days_to_eol
```

Schedule: monthly (cron `0 7 1 * *`), output to PDF for the asset management review.

### Step 3 — Validate
(a) Cross-reference affected devices with the Cisco End-of-Life portal (cisco.com/c/en/us/products/end-of-life-policy.html) to verify the EoL dates.
(b) Compare the affected device count with **Catalyst Center > Compliance** filtered to EOX type (if available).
(c) Verify that `eolDate` parsing produces correct urgency classifications.
(d) Check for devices with `eolStatus` but `eolDate` in the past (already past their lifecycle).

### Step 4 — Operationalize
- Monthly asset review: EoL device list for hardware refresh planning.
- Budget planning: devices approaching EoL within 12 months need replacement budget allocated.
- NIST SA-22 evidence: document each EoL device with either a refresh plan or an approved exception.
- Quarterly executive summary: total devices on EoL software + refresh progress.

Runbook (owner: Asset Management):
1. Review the monthly EoL report.
2. For devices past their EoL date (eolDate in the past): these are the highest risk. Create hardware refresh tickets.
3. For devices approaching EoL (within 180 days): add to the next budget cycle refresh plan.
4. For devices with approved exceptions: verify the compensating controls are still in place (ACLs, segmentation, monitoring).
5. Track refresh progress month-over-month. Goal: zero devices past EoL without a documented exception.

### Step 5 — Troubleshooting

- **`eolStatus` field is null for all devices** — the scripted input may not extract lifecycle data. Check the Catalyst Center API response for lifecycle-related fields. The endpoint may differ from the compliance endpoint used for other SWIM UCs.

- **`eolDate` format doesn't parse** — check the actual date format in the raw events. Adjust the `strptime` format string accordingly.

- **EoL status doesn't match Cisco's published EoL notices** — Catalyst Center's lifecycle database may lag behind Cisco's public announcements. Allow up to 30 days for synchronisation.

- **Very high affected_devices count** — your fleet may have significant technical debt. Prioritise by criticality: internet-facing and CDE devices first, internal access switches last.

- **Same device appears under multiple EoL categories** — the device may have both software EoL (firmware) and hardware EoL (platform). Track separately.

- **No upcoming EoL (all devices current)** — ideal state. Continue monitoring monthly for newly published EoL announcements from Cisco.

- **Want to correlate EoL with PSIRT exposure** — join with UC-5.13.34 (PSIRT Overview): devices on EoL software with active advisories have the highest risk (vulnerability + no patch available).

- **Exception management** — maintain the `catalyst_compliance_exceptions` lookup with `deviceName`, `exception_reason`, `approved_by`, `review_date`. Re-review exceptions quarterly.

Additional operational context for End-of-Life / End-of-Support Software Detection:

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
index=catalyst sourcetype="cisco:dnac:swim" (eolStatus="END_OF_LIFE" OR eolStatus="END_OF_SUPPORT" OR eolStatus="END_OF_SW_MAINTENANCE")
| stats dc(deviceName) as affected_devices values(runningVersion) as versions by deviceFamily, eolStatus, eolDate
| sort eolDate
```

## Visualization

(1) Table: deviceFamily, eolStatus, eolDate, versions, affected_devices — sorted by eolDate (most urgent first). (2) Timeline: EoL dates on a time axis with device counts, showing upcoming deadlines. (3) Single value: total devices on EoL/EoS software (red ≥ 1). (4) Bar chart: affected_devices by deviceFamily.

## Known False Positives

**Devices with approved lifecycle exceptions.** Some EoL devices may have documented risk acceptance (approved to run past their support date with compensating controls). Distinguish by checking the `catalyst_compliance_exceptions` lookup for lifecycle exemptions. Present these as 'acknowledged — exception expires YYYY-MM-DD' rather than open findings.

**EoL status not yet reflected in Catalyst Center.** There may be a lag between Cisco publishing an EoL notice and Catalyst Center updating its lifecycle database. Distinguish by cross-referencing with the Cisco EoL portal directly. No Splunk suppression needed — update Catalyst Center's lifecycle database.

**End-of-SW-Maintenance vs End-of-Life confusion.** End-of-SW-Maintenance means no new maintenance releases but security patches may still be issued. End-of-Life means complete end of all support. Distinguish by the specific `eolStatus` value. Prioritise End-of-Life and End-of-Support over End-of-SW-Maintenance.

**Lab or staging devices running old firmware intentionally.** Test equipment may run old versions for compatibility testing. Distinguish by checking `deviceName` against lab naming conventions. Suppress with `catalyst_excluded_devices` lookup.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Cisco End-of-Life and End-of-Sale Notices](https://www.cisco.com/c/en/us/products/end-of-life-policy.html)
- [Catalyst Center Integration Guide — Custom Scripted Inputs](../../docs/guides/catalyst-center.md#custom-scripted-inputs)
- [NIST SP 800-53 Rev. 5 — SA-22 Unsupported System Components](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=SA-22)
