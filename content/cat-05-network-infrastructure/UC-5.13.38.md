<!-- AUTO-GENERATED from UC-5.13.38.json — DO NOT EDIT -->

---
id: "5.13.38"
title: "Advisory Remediation Progress Tracking"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.38 · Advisory Remediation Progress Tracking

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability, Operations &middot; **Wave:** Run &middot; **Status:** Verified

*We track how quickly your team is fixing each security weakness — showing the number of affected devices declining over time as patches are applied. A flat line means nobody is patching and the risk is unchanged. A declining line proves the investment in upgrades is paying off.*

---

## Description

Tracks the remediation progress for each active security advisory by monitoring how the affected device count decreases over time as firmware upgrades are applied — proving to auditors and management that vulnerability remediation is an ongoing process with measurable results.

## Value

Knowing you have 47 devices affected by a CRITICAL PSIRT (UC-5.13.34) is step one. Proving that count dropped to 12 this week (UC-5.13.38) is the evidence that your firmware campaign is working. This UC provides the remediation velocity metric — how fast are we patching? — which drives the quarterly vulnerability management review and satisfies NIST SI-2 (Flaw Remediation) and ISO 27001 A.8.8 (Management of Technical Vulnerabilities) evidence requirements.

## Implementation

Same `securityadvisory` input as UC-5.13.34. Track `deviceCount` per `advisoryId` over time with `timechart`. Schedule weekly for the security operations review.

## Detailed Implementation

### Prerequisites
- UC-5.13.34 (PSIRT Overview) and UC-5.13.37 (Affected Devices) must be operational — same `securityadvisory` data feed.
- Retain **90+ days** of advisory data to show the full remediation lifecycle from advisory publication to complete patch deployment. This is the evidence chain for NIST SI-2 (Flaw Remediation) and ISO 27001 A.8.8 (Management of Technical Vulnerabilities).
- Define your remediation SLAs by severity: CRITICAL = 72 hours, HIGH = 30 days, MEDIUM = 90 days. These drive the urgency assessment and compliance reporting.

### Step 1 — Configure data collection
Same `securityadvisory` input as UC-5.13.34. No additional configuration. The `deviceCount` field in each advisory event naturally decreases as devices are upgraded to fixed firmware versions — Catalyst Center re-evaluates the mapping on each poll.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| timechart span=1d latest(deviceCount) as affected by advisoryId
```

Why `latest(deviceCount)` per day: shows the end-of-day affected device count for each advisory. A declining line means devices are being patched — the remediation is progressing. A flat line means the campaign stalled — nobody is patching.

Why `by advisoryId`: each advisory gets its own line in the chart. Multiple declining lines converging toward zero is the visual proof that the firmware campaign is working.

For a remediation summary table (executive view):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats earliest(deviceCount) as initial_affected latest(deviceCount) as current_affected latest(advisoryTitle) as title earliest(_time) as first_detected by advisoryId, severity
| eval remediated=initial_affected-current_affected
| eval pct_remediated=if(initial_affected>0, round(remediated*100/initial_affected,1), 100)
| eval days_since_detection=round((now()-first_detected)/86400,0)
| eval sla_status=case(
    severity="CRITICAL" AND days_since_detection > 3 AND current_affected > 0, "SLA BREACH",
    severity="HIGH" AND days_since_detection > 30 AND current_affected > 0, "SLA BREACH",
    current_affected = 0, "COMPLETE",
    1==1, "In progress")
| where initial_affected > 0
| sort severity, -initial_affected
```
This table shows: how many devices were initially affected, how many remain, what percentage has been remediated, and whether the remediation SLA has been breached.

For remediation velocity (rate of device patching):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats earliest(deviceCount) as initial latest(deviceCount) as current earliest(_time) as start latest(_time) as now by advisoryId
| eval elapsed_days=round((now-start)/86400,0)
| eval remediated=initial-current
| eval daily_rate=if(elapsed_days>0, round(remediated/elapsed_days,1), 0)
| eval est_completion_days=if(daily_rate>0, round(current/daily_rate,0), -1)
| where initial > 0 AND current > 0
| sort -est_completion_days
```
`est_completion_days` projects when full remediation will complete at the current patching rate. A negative value means no patching is happening.

Schedule: weekly (cron `0 7 * * 1`), daily during active campaigns. Output to PDF for security review.

### Step 3 — Validate
(a) After a firmware push, verify the `deviceCount` for the corresponding advisory decreases in the next 24 hours. If it doesn't decrease, the upgrade may not have addressed the affected firmware version — verify the fixed version in the advisory matches the target SWIM version.

(b) Compare `current_affected` with **Catalyst Center > Security Advisories > [advisory]** device count. They should match.

(c) Check that `initial_affected` matches the count when the advisory was first detected. The `earliest(deviceCount)` approximates this, but if the TA wasn't running when the advisory was first published, the initial count may be lower than the true initial exposure.

(d) Verify SLA calculations: an advisory with `severity=CRITICAL`, `days_since_detection=5`, and `current_affected > 0` should show `sla_status=SLA BREACH` (CRITICAL SLA = 72 hours = 3 days).

### Step 4 — Operationalize
- Weekly security review: show the remediation summary table. Focus on SLA BREACH rows — these need escalation.
- For ISO 27001 A.8.8: the `pct_remediated` metric and declining device-count trend demonstrate that technical vulnerabilities are being actively managed.
- For NIST SI-2: the remediation velocity metric demonstrates the organisation's flaw remediation capability.

Runbook (owner: Security Operations Manager):
1. Review weekly progress. For each advisory:
   - `pct_remediated > 90%`: nearly complete — verify the remaining devices are scheduled for the next window.
   - `pct_remediated 50-90%`: in progress — is the rate sufficient to meet the SLA?
   - `pct_remediated < 50%`: behind schedule — escalate to firmware management.
   - `sla_status = SLA BREACH`: compliance violation — document the breach and corrective action.
2. Advisories at 100% remediated: archive and close.
3. Advisories with increasing `current_affected`: new devices were added running vulnerable firmware — address in the onboarding process (PnP should deploy fixed versions by default).
4. `est_completion_days > 30` for a CRITICAL advisory: the current patching rate is too slow. Request additional maintenance windows or emergency change authority.

### Step 5 — Troubleshooting

- **Device count increases instead of decreasing** — new devices running vulnerable firmware were added to inventory. This is a genuine exposure increase, not a data error.

- **Device count drops to 0 then comes back** — API timing issue. The advisory-device mapping may be stale during certain polls. Use `latest()` over a 2-day window for stability.

- **Can't determine initial count** — the advisory was already active before you started collecting data. `earliest(deviceCount)` gives the count from your first poll, not from advisory publication. For precise initial counts, check the Cisco PSIRT publication date and correlate with your first advisory poll after that date.

- **Remediation progress doesn't match SWIM upgrade status** — SWIM tracks upgrade distribution; advisory remediation tracks vulnerability exposure. They should correlate but may lag by 24 hours as Catalyst Center re-evaluates firmware versions.

- **Advisory severity changed** — Cisco may reclassify. The advisory may move from HIGH to CRITICAL (increased threat intelligence) or from CRITICAL to HIGH (mitigating factors discovered). Track severity at detection time vs current severity.

- **Many advisories to track** — filter to CRITICAL only for the executive view. Include HIGH for the full security ops view.

- **No remediation progress in 30+ days** — your firmware upgrade cadence is too slow, or the affected devices can't be upgraded (EOL hardware). Document the constraint and implement compensating controls.

- **Want to show ROI of firmware campaigns** — overlay the remediation trend with firmware campaign dates and costs. Each declined advisory-device pair is a risk reduction that can be quantified.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| timechart span=1d latest(deviceCount) as affected by advisoryId
```

## Visualization

(1) Line chart: deviceCount per CRITICAL/HIGH advisory over time (each advisory as a series, declining lines = progress). (2) Table: advisoryId, initial_affected, current_affected, remediated_pct. (3) Single value: percentage of CRITICAL devices remediated. (4) Annotations: mark firmware push dates.

## Known False Positives

**Remediation progress appearing to regress when new devices are added to Catalyst Center.** When new devices are onboarded, they may be affected by existing advisories, increasing the `current_affected` count and making it appear that remediation progress has regressed. Distinguish by separating newly onboarded devices from the existing fleet: track `dc(deviceId)` over time and correlate with inventory additions. Suppress by computing remediation progress as a percentage of the original affected fleet, excluding devices onboarded after the advisory was first detected.

**Device remediated by firmware upgrade but compliance re-scan not yet complete.** A device that has been upgraded to a fixed version may still appear as affected until Catalyst Center's next PSIRT scan re-evaluates it. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:swim"` or `index=catalyst sourcetype="cisco:dnac:device"` for version changes. Suppress by allowing one scan cycle (3600s) after a device upgrade before counting it as still-affected.

**Compensating control applied but device still listed as affected.** Catalyst Center tracks affected devices by software version, not by compensating controls. A device with an ACL or IPS rule mitigating the vulnerability will still appear in the affected list. Distinguish by cross-referencing with the `catalyst_advisory_exceptions` lookup. Do not suppress from the advisory view — note the compensating control status alongside the advisory.

**Advisory with no available fix showing zero remediation progress.** Some advisories affect devices running software where no fixed version is available yet. Remediation progress will remain at 0% indefinitely. Distinguish by checking the advisory's `fixedVersions` — if empty, no remediation is possible. Suppress by separating advisories with available fixes from those without in the remediation tracking dashboard.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
