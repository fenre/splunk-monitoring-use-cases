<!-- AUTO-GENERATED from UC-5.13.35.json — DO NOT EDIT -->

---
id: "5.13.35"
title: "Critical/High PSIRT Alerting"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.35 · Critical/High PSIRT Alerting

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We set up an urgent alarm for when a serious security weakness is found in your network equipment. If a dangerous vulnerability is discovered that affects your devices, your security team gets notified within the hour so they can patch or protect the equipment before attackers can exploit it.*

---

## Description

Fires an alert when a new CRITICAL or HIGH severity Cisco security advisory (PSIRT) is detected that affects devices in your managed infrastructure, providing the advisory title, CVE, affected device count, and available fixes for immediate security response.

## Value

A new CRITICAL PSIRT affecting your infrastructure is a security emergency. The 2023 IOS-XE Web UI vulnerability (CVE-2023-20198) went from zero-day to mass exploitation in 48 hours. This alert ensures your security team knows about critical advisories within the hourly poll cycle — not days later when the trade press picks it up. The alert payload includes the affected device count and available fixed versions, so the team can immediately assess blast radius and begin emergency patching. For PCI DSS 6.3.1, this demonstrates automated vulnerability identification.

## Implementation

Same `securityadvisory` input as UC-5.13.34. Schedule as alert: cron `0 * * * *` (hourly), trigger when results > 0. Throttle by `advisoryId` for 7 days. Route CRITICAL to high-urgency page, HIGH to email/Slack.

## Detailed Implementation

### Prerequisites
- UC-5.13.34 (PSIRT Overview) must be operational — same `securityadvisory` data feed.
- Decide on alert routing before enabling: CRITICAL PSIRTs should page the network security lead immediately — this is a security emergency with potential active exploitation. HIGH PSIRTs should notify via Slack/email during business hours. MEDIUM and below are informational (covered by UC-5.13.34's weekly report, not this real-time alert).
- For PCI DSS 6.3.1 (Identification of Security Vulnerabilities), document this alert in your PCI controls matrix as the automated vulnerability identification mechanism for network infrastructure.
- Maintain a `catalyst_advisory_exceptions` lookup for advisories that have been assessed and accepted (e.g., a HIGH advisory affecting a non-production lab environment). This prevents re-alerting on acknowledged risks.

### Step 1 — Configure data collection
Same `securityadvisory` input as UC-5.13.34. No additional configuration. For fastest detection, consider reducing the poll interval from 3600s (hourly) to 1800s (30 minutes) for the advisory input specifically — Cisco publishes critical PSIRTs without warning, and every hour of detection delay is an hour of exposure.

Verification that CRITICAL/HIGH advisories exist in the data:
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH") earliest=-30d
| stats dc(advisoryId) as advisories sum(deviceCount) as affected by severity
```
If no results, either your fleet is not affected by any current CRITICAL/HIGH advisories (ideal) or the `severity` field has different values — check `| stats values(severity)`.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats latest(advisoryTitle) as title latest(cveId) as cve latest(deviceCount) as affected_devices latest(fixedVersions) as fixes by advisoryId, severity
| where affected_devices > 0
| sort case(severity="CRITICAL",1,1==1,2) -affected_devices
```

Why `severity IN ("CRITICAL","HIGH")` only: MEDIUM and LOW advisories rarely require emergency response — they're covered in UC-5.13.34's weekly review. Alerting on all severities would cause alert fatigue (a typical fleet has 20–40 MEDIUM/LOW advisories at any time). The CRITICAL/HIGH filter keeps this alert high-signal.

Why `where affected_devices > 0`: advisories that don't affect any device in your inventory are informational but not actionable. An advisory for Catalyst 2960X when your fleet is all 9300s produces a `deviceCount=0` event — filtering to `> 0` ensures every alert is relevant to YOUR network.

Why `latest()` per advisoryId: deduplicates across poll cycles. Each poll returns the full advisory set; `latest()` gives the current state per advisory.

Why include `fixedVersions`: the security team's first question after "what's the vulnerability?" is "is there a patch?" Including the fix information in the alert body saves a round-trip to the Cisco PSIRT portal.

Schedule as Alert:
- Cron: `0 * * * *` (hourly — aligned with the advisory poll interval)
- Time range: `-2h to now` (covers 2 poll cycles for reliability)
- Trigger: "Number of results > 0"
- Throttle: by `advisoryId` for `7d` (once you know about an advisory, you don't need re-notification for a week — the remediation tracking is in UC-5.13.38)
- Severity: Critical (for CRITICAL results), High (for HIGH-only results)

For differentiated routing (separate alert rules):
```spl
-- Alert 1: CRITICAL only (highest urgency — page immediately)
index=catalyst sourcetype="cisco:dnac:securityadvisory" severity="CRITICAL"
| stats latest(advisoryTitle) as title latest(cveId) as cve latest(deviceCount) as affected latest(fixedVersions) as fixes by advisoryId
| where affected > 0
```
```spl
-- Alert 2: HIGH only (elevated urgency — business hours notification)
index=catalyst sourcetype="cisco:dnac:securityadvisory" severity="HIGH"
| stats latest(advisoryTitle) as title latest(cveId) as cve latest(deviceCount) as affected latest(fixedVersions) as fixes by advisoryId
| where affected > 0
```

### Step 3 — Validate
(a) Check the Cisco PSIRT portal (`sec.cloudapps.cisco.com/security/center/publicationListing.x`) for recently published advisories. Cross-reference with the Splunk data — any CRITICAL/HIGH advisory that affects Cisco Catalyst platforms should appear in the search results if your fleet runs affected firmware.

(b) Verify `deviceCount` accuracy: pick a CRITICAL advisory from the results and compare `affected_devices` with **Catalyst Center > Security Advisories > [advisory detail] > Affected Devices**. The counts should match.

(c) Throttle test: trigger the alert, then verify it doesn't re-fire for the same `advisoryId` within 7 days. After 7 days, it should re-alert if the advisory hasn't been remediated — this is intentional persistence for unremediated vulnerabilities.

(d) Alert action test: temporarily modify the search to trigger on MEDIUM advisories (which likely exist), verify the PagerDuty/Slack notification arrives with the correct payload (advisoryId, title, CVE, affected_devices, fixes), then revert to CRITICAL/HIGH only.

(e) Vendor UI parity: compare the CRITICAL/HIGH advisory list with **Catalyst Center > Security Advisories** filtered to Critical and High severity.

### Step 4 — Operationalize
Alerting:
- **CRITICAL**: high-urgency PagerDuty page to the network security lead AND `#incident-security` Slack channel. Include: advisoryId, title, CVE, affected_devices count, fixed versions, and a direct link to the Cisco PSIRT publication URL (`https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/<advisoryId>`).
- **HIGH**: low-urgency PagerDuty notification to the security operations team + `#security-ops` Slack channel (business hours only: `| where date_hour >= 7 AND date_hour <= 19`).
- **Both**: include a link to UC-5.13.37 (Affected Devices) for the remediation target list.

Runbook (owner: Network Security Operations):
1. Receive alert. Note severity, advisory title, CVE, and affected device count.
2. **Read the full advisory**: open the Cisco PSIRT publication URL. Understand the exploitation vector — is it remotely exploitable? Does it require authentication? Is there active exploitation in the wild?
3. **Check for a fix**: inspect the `fixes` field. If a patched firmware version is available:
   - For CRITICAL with active exploitation: declare a security incident. Plan emergency firmware push within 24 hours. Coordinate with the change advisory board for emergency change approval.
   - For CRITICAL without active exploitation: plan firmware push within 72 hours via standard change process.
   - For HIGH: plan firmware push within 30 days via the next scheduled maintenance window.
4. **If no fix available** (zero-day or recently published):
   - Read the Cisco advisory for workarounds (typically ACL changes, feature disablement, or access-list restrictions).
   - For internet-facing devices: apply workarounds within 24 hours for CRITICAL, 72 hours for HIGH.
   - For internal-only devices: apply within 7 days.
   - Track the workaround deployment with UC-5.13.38.
5. **Assess blast radius**: open UC-5.13.37 (Affected Devices) to see exactly which devices need patching. Group by `platformId` — same platform family = same upgrade image.
6. **Create the remediation plan**: for each affected platform family, identify the target fixed version, verify the image is in the SWIM repository, and create the distribution task.
7. **Track remediation**: use UC-5.13.38 (Advisory Remediation Progress) to monitor the declining affected-device count as patches are applied.
8. **Document**: for PCI DSS 6.3.1 evidence, record the full timeline: advisory publication date → Splunk detection date → assessment date → remediation plan date → remediation completion date.

### Step 5 — Troubleshooting

- **Alert never fires** — either no CRITICAL/HIGH advisories affect your fleet (good!) or the `severity` field values don't match the filter. Check `| stats values(severity)` for the actual strings. Common variants: `Critical` vs `CRITICAL`, `High` vs `HIGH`. Adjust the filter accordingly.

- **Alert fires for advisories with `deviceCount=0`** — the `where affected_devices > 0` filter is missing from the search. Re-add it. Advisories with zero affected devices are informational but not actionable.

- **Same advisory re-alerts after 7 days** — throttle expired. This is intentional — if the advisory hasn't been remediated in 7 days, re-alerting is appropriate. It prevents "set and forget" on unpatched vulnerabilities.

- **`fixedVersions` is empty** — no patch is available yet. This is a zero-day or recently published advisory. Apply workarounds from the Cisco publication. Track the fix availability via Cisco's security advisory RSS feed or email subscription.

- **Advisory severity disagrees with NVD/CVSS score** — Cisco assigns its own severity based on product-specific impact assessment, which may differ from the NIST NVD CVSS base score. Use Cisco's severity for operational response (they know the exploitability of their own products). Reference CVSS for compliance reporting if your framework requires it.

- **Many CRITICAL advisories appear simultaneously after Catalyst Center upgrade** — the upgrade may have expanded advisory detection to cover more CVEs or more device platforms. Verify each is genuinely new (check `publicationDate`). Advisories published before the upgrade were always relevant — the upgrade just made Catalyst Center aware of them.

- **Alert action not triggering** — check `index=_internal sourcetype=splunkd component=AlertManager` for the alert name. Common issues: PagerDuty integration key expired, Slack webhook URL changed, email relay misconfigured.

- **Want to differentiate internet-facing vs internal devices** — add a `device_exposure` lookup (deviceName → exposure_level: internet_facing, dmz, internal) and create a separate high-urgency alert for internet-facing devices affected by CRITICAL advisories: `| lookup device_exposure deviceName OUTPUT exposure_level | where exposure_level="internet_facing"`. Internet-facing + CRITICAL = highest possible urgency.

- **Advisory affects devices managed by multiple Catalyst Center clusters** — if you run multiple Catalyst Center instances, each produces its own advisory data. Deduplicate across clusters by `advisoryId` and sum `deviceCount` for the fleet-wide view.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" (severity="CRITICAL" OR severity="HIGH")
| stats latest(advisoryTitle) as title latest(cveId) as cve latest(deviceCount) as affected_devices latest(fixedVersions) as fixes by advisoryId, severity
| where affected_devices > 0
| sort case(severity="CRITICAL",1,1==1,2) -affected_devices
```

## Visualization

(1) Alert payload: advisoryId, advisoryTitle, severity, cveId, deviceCount, fixedVersions. (2) Single value: CRITICAL advisory count (red ≥ 1). (3) Drilldown to UC-5.13.37 (affected devices) for remediation targeting.

## Known False Positives

**Critical/High advisory affecting only lab or end-of-life devices.** A CRITICAL or HIGH PSIRT advisory may affect devices that are in a lab environment or have already been scheduled for decommissioning. Distinguish by checking whether the affected `deviceId` values correspond to devices in non-production `siteId` values or devices flagged for EOL. Suppress by maintaining a `catalyst_excluded_devices` lookup and filtering those devices from the critical alerting, while tracking them in a separate risk dashboard.

**Advisory with compensating controls already in place.** The vulnerability may require specific network conditions (e.g., exposed management interface) that are already mitigated by ACLs, segmentation, or other compensating controls. Distinguish by reviewing the advisory's exploitation conditions and verifying whether the compensating controls exist in the network. Suppress by maintaining a `catalyst_advisory_exceptions` lookup with advisoryId, deviceName, compensating control, and review date.

**Catalyst Center severity differs from published PSIRT base score.** Catalyst Center may assess a different severity than the published PSIRT based on local context (device exposure, software configuration). Distinguish by comparing the `severity` field in Splunk with the authoritative PSIRT listing at `https://sec.cloudapps.cisco.com/security/center/publicationListing.x`. No suppression needed — use the authoritative source for final risk assessment.

**Advisory re-detected after Catalyst Center PSIRT database update.** A database update may re-surface previously assessed advisories. Distinguish by checking the advisory's `first_seen` timestamp in Splunk against the database update date. Suppress by tracking `| stats earliest(_time) as first_seen by advisoryId` and alerting only on advisories with `first_seen` within the current reporting window.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](../../docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
