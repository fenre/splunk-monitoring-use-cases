<!-- AUTO-GENERATED from UC-5.13.56.json — DO NOT EDIT -->

---
id: "5.13.56"
title: "Firmware Non-Compliance Detection (Running vs Golden Image)"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.56 · Firmware Non-Compliance Detection (Running vs Golden Image)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Compliance, Configuration &middot; **Wave:** Walk &middot; **Status:** Verified

*We check which network devices are running the approved software version and which ones are behind. Devices running old software may have security holes or bugs. We list exactly which ones need updating and what version they should be upgraded to, so your team can plan the updates efficiently.*

---

## Description

Identifies devices running firmware that doesn't match the designated golden image in Catalyst Center SWIM — listing each non-compliant device with its current version and the target version it should be upgraded to, enabling targeted firmware upgrade campaigns for NIST CM-2 and SI-2 compliance.

## Value

UC-5.13.55 shows what's running. This UC shows what's *wrong*. A device running IOS-XE 17.6.5 when the golden image is 17.9.4a is missing 3 versions of security patches and bug fixes. The per-device list with `running` vs `target` version is exactly what the SWIM distribution engineer needs to build an upgrade task in Catalyst Center. For NIST CM-2 (Baseline Configuration), this is the evidence that baseline enforcement is actively monitored. For SI-2 (Flaw Remediation), the count of non-compliant devices is the remediation backlog metric that auditors track.

## Implementation

Requires a custom scripted input for SWIM data (see `docs/guides/catalyst-center.md` § Custom Scripted Inputs). The TA does not include a native SWIM modular input. Filter to `imageCompliance="NON_COMPLIANT"` for the remediation work list. Schedule weekly for the firmware management review.

## Detailed Implementation

### Prerequisites
- A custom scripted input for SWIM compliance data must be deployed on the Heavy Forwarder. The native TA does not include a SWIM modular input. See `docs/guides/catalyst-center.md` § Custom Scripted Inputs for the script template, `inputs.conf` stanza, and deployment instructions.
- Golden images must be designated in **Catalyst Center > SWIM > Golden Images** for each device family. Without golden image designations, all devices return NOT_APPLICABLE.
- Service account with **NETWORK-ADMIN-ROLE** for SWIM compliance data.
- For NIST CM-2 / SI-2 compliance, document the golden image policy: which version is approved for each platform, when it was designated, and the expected remediation timeline for non-compliant devices.

### Step 1 — Configure data collection
Deploy the SWIM compliance scripted input:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_swim/bin/poll_swim_compliance.py]
interval = 3600
sourcetype = cisco:dnac:swim
index = catalyst
disabled = 0
```

The script polls `GET /dna/intent/api/v1/compliance/detail?complianceType=IMAGE` and outputs one JSON event per device with `imageCompliance`, `runningVersion`, `targetVersion`, `deviceName`, `deviceFamily`.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:swim" earliest=-2h
| stats dc(deviceName) as devices by imageCompliance
```
You should see rows for COMPLIANT and NON_COMPLIANT.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT"
| stats latest(runningVersion) as running latest(targetVersion) as target by deviceName, deviceFamily
| table deviceName, deviceFamily, running, target
| sort deviceFamily, deviceName
```

Why `latest()` per device: deduplicates across poll cycles. Each poll returns the full compliance state; `latest()` gives the current state.

Why `by deviceName, deviceFamily`: the output is a device-level work list. Group by `deviceFamily` so the firmware engineer can batch upgrades per platform (same image applies to all devices of the same family).

For fleet-level compliance ratio:
```spl
index=catalyst sourcetype="cisco:dnac:swim"
| stats dc(eval(if(imageCompliance="COMPLIANT",deviceName,null()))) as compliant dc(eval(if(imageCompliance="NON_COMPLIANT",deviceName,null()))) as noncompliant
| eval total=compliant+noncompliant
| eval pct=round(compliant*100/total,1)
```

Schedule: weekly (cron `0 7 * * 1`), output as CSV for the firmware upgrade team.

### Step 3 — Validate
(a) Compare the non-compliant device list with **Catalyst Center > SWIM > Image Compliance** filtered to NON_COMPLIANT. The device lists should match.
(b) Verify `targetVersion` matches the golden image designated in SWIM for that device family.
(c) Spot-check `runningVersion` against `show version` on a sample device.
(d) Vendor UI parity: compare the compliance ratio with **Catalyst Center > SWIM > Compliance Summary**.

### Step 4 — Operationalize
- Firmware upgrade work list: export the non-compliant device table as CSV for the SWIM upgrade team.
- Track remediation progress with UC-5.13.57 (Upgrade Progress) and UC-5.13.38 (Advisory Remediation).
- Monthly report: compliance ratio trend for NIST CM-2 / SI-2 evidence.
- Prioritise by `deviceFamily` — upgrade the largest non-compliant population first for maximum impact.

Runbook (owner: Firmware Management):
1. Review the weekly non-compliant device list.
2. Group by `deviceFamily`. For each family: verify the golden image is available in the SWIM image repository.
3. Create a SWIM distribution task in **Catalyst Center > SWIM > Distribute Image** targeting the non-compliant devices.
4. Schedule the upgrade during the next maintenance window.
5. After upgrade: verify devices transition to COMPLIANT in the next poll cycle.

### Step 5 — Troubleshooting

- **No `cisco:dnac:swim` events** — the custom scripted input is not deployed. Follow `docs/guides/catalyst-center.md` § Custom Scripted Inputs for deployment.

- **All devices show NOT_APPLICABLE** — golden images are not designated in SWIM. Configure golden images in **Catalyst Center > SWIM > Golden Images** per device family.

- **`runningVersion` disagrees with `show version`** — Catalyst Center's inventory may be stale. Force an inventory resync in **Catalyst Center > Provision > Inventory > Resync**.

- **`targetVersion` is empty** — the golden image is not set for that device family in SWIM.

- **Compliance ratio shows 0% — all non-compliant** — golden image was just designated; no devices have been upgraded yet. This is the starting point for a firmware campaign.

- **Device shows COMPLIANT but running an old version** — the golden image designation may have been lowered to match what's already deployed. Check the golden image version in SWIM.

- **`imageCompliance` field name differs** — check `| fieldsummary | search field=*compliance*` for the actual field name in your scripted input output.

- **Want to track upgrade progress over time** — use `| timechart span=1d dc(eval(if(imageCompliance="NON_COMPLIANT",deviceName,null()))) as noncompliant`. A declining line means the campaign is progressing.

Additional operational context for Firmware Non-Compliance Detection (Running vs Golden Image):

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
index=catalyst sourcetype="cisco:dnac:swim" imageCompliance="NON_COMPLIANT"
| stats latest(runningVersion) as running latest(targetVersion) as target by deviceName, deviceFamily
| table deviceName, deviceFamily, running, target
| sort deviceFamily, deviceName
```

## Visualization

(1) Table: deviceName, deviceFamily, running, target — the upgrade work list. (2) Bar chart: non-compliant device count by deviceFamily. (3) Single value: total non-compliant devices (red ≥ 1). (4) Pie: compliant vs non-compliant across the fleet. (5) Trend: `| timechart span=1w dc(eval(if(imageCompliance="NON_COMPLIANT",deviceName,null()))) as noncompliant` for remediation progress.

## Known False Positives

**Golden image recently updated but devices not yet upgraded.** When the golden image designation changes in SWIM, all devices running the old version become NON_COMPLIANT. This is expected and intentional — it creates the upgrade backlog. Do not suppress — track as the planned remediation work.

**Devices in the upgrade queue showing NON_COMPLIANT.** Devices scheduled for upgrade in the next maintenance window are technically non-compliant but have a planned remediation date. Distinguish by cross-referencing with UC-5.13.57 (Upgrade Progress) for devices with active upgrade tasks. Present as 'scheduled for upgrade' rather than 'non-compliant.'

**AP firmware managed separately from switch firmware.** APs may have different golden image designations than switches and WLCs. Distinguish by checking `deviceFamily`. Present AP compliance separately from switch/router compliance.

**Device running a newer version than the golden image.** Occasionally a device is upgraded to a version ahead of the designated golden image (e.g., emergency security patch). This shows as NON_COMPLIANT even though the device is on a better version. Distinguish by comparing version numbers: `| eval ahead=if(running > target, 1, 0)`.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center SWIM — Golden Image Management](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center/swim-guide.html)
- [Catalyst Center Integration Guide — Custom Scripted Inputs](../../docs/guides/catalyst-center.md#custom-scripted-inputs)
- [NIST SP 800-53 Rev. 5 — CM-2 Baseline Configuration](https://csrc.nist.gov/projects/cprt/catalog#/cprt/framework/version/SP_800_53_5_1_0/home?element=CM-2)
