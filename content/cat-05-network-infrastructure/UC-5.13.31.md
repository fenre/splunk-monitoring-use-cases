<!-- AUTO-GENERATED from UC-5.13.31.json — DO NOT EDIT -->

---
id: "5.13.31"
title: "Compliance by Rule/Policy Category"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.13.31 · Compliance by Rule/Policy Category

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We sort the configuration problems by type — is the issue a wrong software version, a changed setting, or a security vulnerability? This tells your team whether they need to push a software update, fix a setting, or patch a security hole, because each type of problem has a different team responsible and a different fix.*

---

## Description

Breaks down non-compliance by policy category — RUNNING_CONFIG, IMAGE, PSIRT, EOX, NETWORK_SETTINGS — showing which type of compliance check accounts for the most violations, so remediation effort is directed at the largest gap rather than spread thinly across all categories.

## Value

UC-5.13.28 tells you *how many* devices are non-compliant. This UC tells you *why*. If 80% of violations are RUNNING_CONFIG, the team needs to push golden templates — that's a change management action. If 80% are IMAGE, the priority is a firmware upgrade campaign — that's a SWIM task. If 80% are PSIRT, there's a critical vulnerability exposure — that's a security emergency. Each compliance type has a different remediation owner, different timeline, and different cost. This breakdown ensures budget and effort go to the category that moves the compliance percentage the most, and for compliance evidence it shows assessors that you understand the composition of your non-compliance, not just the headline number.

## Implementation

Same `compliance` input as UC-5.13.28. Filters to NON_COMPLIANT only. Groups by `complianceType` to show which policy families have the most violations. Schedule weekly alongside UC-5.13.28 for the compliance review.

## Detailed Implementation

### Prerequisites
- UC-5.13.28 (Compliance Status Overview) must be operational — same `compliance` data feed.
- Understand the Catalyst Center compliance type taxonomy — this is the key knowledge for interpreting results:
  - **RUNNING_CONFIG**: device running configuration vs golden template. The most common and most actionable type. Failures indicate configuration drift — someone made a manual CLI change, or the golden template wasn't pushed after an update. Remediation owner: Change Management / Network Engineering.
  - **IMAGE**: device firmware version vs designated golden image. Failures indicate firmware non-compliance — the device isn't running the approved IOS-XE version. See UC-5.13.56 for firmware-specific analysis. Remediation owner: Firmware Management / SWIM team.
  - **PSIRT**: device firmware vs Cisco PSIRT (security advisory) database. Failures indicate the device is affected by a known vulnerability and needs patching. See UC-5.13.34–39 for advisory-specific analysis. Remediation owner: Security Operations.
  - **EOX**: device hardware/software vs Cisco End-of-Life announcements. Failures indicate the device is past its support lifecycle — no more patches will ever be released. See UC-5.13.59. Remediation owner: Asset Management / Procurement.
  - **NETWORK_SETTINGS**: device settings vs Catalyst Center network design settings (IP addressing, DNS servers, NTP, etc.). Less common; depends on how thoroughly Catalyst Center design settings are configured. Remediation owner: Network Architecture.

### Step 1 — Configure data collection
Same `compliance` input as UC-5.13.28. No additional configuration.

Confirm multiple compliance types are present:
```spl
index=catalyst sourcetype="cisco:dnac:compliance" earliest=-24h
| stats dc(deviceName) as devices by complianceType, complianceStatus
| sort complianceType
```
You should see multiple `complianceType` values with both COMPLIANT and NON_COMPLIANT status. If only RUNNING_CONFIG appears, other compliance types may not be configured in Catalyst Center — check **Catalyst Center > Compliance > Policies** for enabled policy types.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| stats dc(deviceName) as affected_devices by complianceType
| eventstats sum(affected_devices) as total_violations
| eval pct=round(affected_devices*100/total_violations,1)
| sort -affected_devices
```

Why `dc(deviceName)` not `count`: the search window may cover multiple polls, and the same device appears in every poll. `dc(deviceName)` gives the actual number of unique non-compliant devices per type — the operationally meaningful count.

Why `eventstats sum` for the percentage: computes the total across all types in a single pass, so each row shows its share of the total violation pool. This immediately answers: "What percentage of our compliance failures are configuration drift vs firmware vs security advisories?"

Why NON_COMPLIANT only: COMPLIANT devices are the goal state, not the problem. Showing only violations focuses the dashboard on what needs fixing.

For a complete COMPLIANT vs NON_COMPLIANT breakdown per type (more comprehensive, useful for assessor walkthroughs):
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| where complianceStatus IN ("COMPLIANT","NON_COMPLIANT")
| stats dc(eval(if(complianceStatus="COMPLIANT",deviceName,null()))) as compliant dc(eval(if(complianceStatus="NON_COMPLIANT",deviceName,null()))) as non_compliant by complianceType
| eval total=compliant+non_compliant
| eval compliant_pct=round(compliant*100/total,1)
| sort compliant_pct
```
This shows the compliance rate PER TYPE — useful for identifying which policy family has the worst compliance rate, not just the most violations.

For per-type trending (how is each compliance type improving or degrading?):
```spl
index=catalyst sourcetype="cisco:dnac:compliance"
| where complianceStatus IN ("COMPLIANT","NON_COMPLIANT")
| timechart span=1w dc(eval(if(complianceStatus="NON_COMPLIANT",deviceName,null()))) as non_compliant by complianceType
```

For remediation owner assignment:
```spl
<base search>
| eval owner=case(
    complianceType="RUNNING_CONFIG", "Change Management",
    complianceType="IMAGE", "Firmware Management",
    complianceType="PSIRT", "Security Operations",
    complianceType="EOX", "Asset Management",
    complianceType="NETWORK_SETTINGS", "Network Architecture",
    1==1, "Unassigned")
| table complianceType, affected_devices, pct, owner
```

Schedule as Report: weekly (cron `0 7 * * 1`), output alongside UC-5.13.28 on the Compliance Posture dashboard.

### Step 3 — Validate
(a) Compare the per-type breakdown with **Catalyst Center > Compliance** filtered by type. The device counts per type should match within one poll cycle.

(b) Verify all expected compliance types appear. If only RUNNING_CONFIG shows, other types may not be configured in Catalyst Center — check **Catalyst Center > Compliance > Policies** for enabled policy types. Also check: some compliance types require specific Catalyst Center features (PSIRT requires Security Advisories feature; EOX requires lifecycle tracking; IMAGE requires SWIM golden image designation).

(c) Note: the total across all types may be GREATER than UC-5.13.28's total non-compliant device count because one device can fail multiple types (non-compliant for both RUNNING_CONFIG and IMAGE). Each type is counted independently.

(d) Cross-reference IMAGE violations with UC-5.13.56 (Firmware Non-Compliance) — the device counts should approximately match.

(e) Cross-reference PSIRT violations with UC-5.13.34 (PSIRT Overview) — the device counts should correlate.

(f) Vendor UI parity: compare the per-type breakdown with **Catalyst Center > Compliance** using the compliance type filter.

### Step 4 — Operationalize
Dashboard placement (on the "Compliance Posture" dashboard, next to UC-5.13.28's donut chart):
- Pie chart: affected_devices by complianceType — at-a-glance view of which category dominates violations.
- Table with drilldown: click a type → filter UC-5.13.33 (Violation Detail) to that complianceType for the specific failing rules.
- Add the `owner` column from the remediation-owner variant so the dashboard directly assigns responsibility.

Remediation prioritisation (weekly compliance review):
1. Review which compliance type has the most violations.
2. Assign remediation ownership by type:
   - **RUNNING_CONFIG** → Change Management: schedule golden template re-push. Coordinate with CAB for change approval.
   - **IMAGE** → Firmware Management: plan SWIM upgrade campaign (UC-5.13.56, UC-5.13.57). Estimate maintenance window duration.
   - **PSIRT** → Security Operations: assess advisory severity (UC-5.13.34–39). Emergency patch for CRITICAL, planned upgrade for HIGH/MEDIUM.
   - **EOX** → Asset Management: plan hardware refresh. Budget for replacement devices in the next procurement cycle.
   - **NETWORK_SETTINGS** → Network Architecture: review Catalyst Center design intent settings for accuracy.
3. Track per-type compliance_pct over time with the trending variant. Each type should have its own SLO (RUNNING_CONFIG may target 95%, IMAGE may target 80% due to upgrade cadence).

For assessor walkthroughs:
- Show the complete COMPLIANT vs NON_COMPLIANT per-type table.
- For each non-compliant type, demonstrate the remediation pipeline: detection (this UC) → alerting (UC-5.13.29) → detail drill-down (UC-5.13.33) → remediation tracking (UC-5.13.30 trending).
- Export as evidence for NIST CM-6 (demonstrates monitoring across configuration categories, not just a single dimension).

### Step 5 — Troubleshooting

- **Only one compliance type appears** — other types may not be configured in Catalyst Center. Check **Catalyst Center > Compliance > Policies** for enabled types. To enable IMAGE compliance: designate golden images in **SWIM > Golden Image**. To enable PSIRT: enable Security Advisories feature. To enable EOX: enable lifecycle tracking.

- **IMAGE violations dominate** — expected in environments with delayed firmware campaigns. Track IMAGE separately from RUNNING_CONFIG. IMAGE is typically an operations timeline issue (planned upgrades), while RUNNING_CONFIG is a security/change-management issue (unexpected configuration drift).

- **PSIRT type is absent** — PSIRT compliance checking may require a separate Catalyst Center license or feature enablement. Check **Catalyst Center > Security Advisories** for feature availability.

- **Total affected_devices across types > total non-compliant devices in UC-5.13.28** — expected. A single device can be non-compliant for multiple types (e.g., both RUNNING_CONFIG and IMAGE). Each type counts independently. The total shows the remediation workload, not the unique device count.

- **EOX violations for devices with planned replacements** — use the `catalyst_compliance_exceptions` lookup to flag these as 'acknowledged with replacement date YYYY-MM-DD' rather than open violations.

- **NETWORK_SETTINGS type shows high violations** — this type checks device settings against Catalyst Center's design intent (IP pools, DNS, NTP, etc.). If the design settings in Catalyst Center are incomplete or incorrect, many devices appear non-compliant. Review **Catalyst Center > Design > Network Settings** for accuracy before acting on NETWORK_SETTINGS violations.

- **Compliance type names changed after Catalyst Center upgrade** — check `| stats values(complianceType)` and update dashboard labels and SPL filters if needed.

- **No data for some types on certain device families** — expected. APs typically don't support IMAGE or EOX compliance checks. The absence is correct, not an error — those compliance types are not applicable to AP platforms.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT"
| stats dc(deviceName) as affected_devices by complianceType
| eventstats sum(affected_devices) as total_violations
| eval pct=round(affected_devices*100/total_violations,1)
| sort -affected_devices
```

## Visualization

(1) Pie or donut: affected_devices by complianceType — shows the relative share of each violation type. (2) Table: complianceType, affected_devices, pct — sorted by count. (3) Drilldown: click RUNNING_CONFIG → filter UC-5.13.33 (Violation Detail). Click IMAGE → link to UC-5.13.56 (Firmware Non-Compliance). (4) Stacked bar: COMPLIANT vs NON_COMPLIANT by complianceType for a complete per-type posture view.

## Known False Positives

**NOT_APPLICABLE compliance types inflating the denominator.** If NOT_APPLICABLE devices are counted alongside COMPLIANT and NON_COMPLIANT, the per-type breakdown becomes misleading. This UC filters to NON_COMPLIANT only, avoiding this. Be aware that some device families don't support certain compliance types (e.g., IMAGE compliance for APs), so the affected-device count for those types will be naturally zero.

**IMAGE non-compliance dominated by devices awaiting scheduled upgrade.** Devices in the SWIM upgrade queue show IMAGE non-compliance even though the upgrade is planned. Distinguish by cross-referencing with UC-5.13.57 (Upgrade Progress). Track IMAGE non-compliance separately from RUNNING_CONFIG — IMAGE is often an operations timeline issue, while RUNNING_CONFIG is a security/change-management issue.

**PSIRT non-compliance for low-severity advisories.** Catalyst Center may flag PSIRT non-compliance for informational advisories that don't require immediate action. Distinguish by checking the advisory severity in UC-5.13.34. Filter PSIRT violations to `severity IN ("CRITICAL","HIGH")` for security-focused views.

**EOX non-compliance for devices with approved lifecycle exceptions.** End-of-life devices may have documented risk acceptance. Distinguish by checking the `catalyst_compliance_exceptions` lookup. Present excepted devices with their exception date and review schedule.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Compliance endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-compliance-status)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [NIST SP 800-53 Rev. 5 — CM-6 Configuration Settings](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-6)
