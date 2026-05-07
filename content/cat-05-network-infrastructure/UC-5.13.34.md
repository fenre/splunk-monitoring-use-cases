<!-- AUTO-GENERATED from UC-5.13.34.json — DO NOT EDIT -->

---
id: "5.13.34"
title: "Security Advisory (PSIRT) Overview"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.13.34 · Security Advisory (PSIRT) Overview

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security, Vulnerability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We show you all the known security weaknesses that affect your network equipment, ranked by how serious they are and how many devices are at risk. This helps your security team focus on patching the most dangerous vulnerabilities first.*

---

## Description

Provides a complete overview of all Cisco security advisories (PSIRTs) affecting devices managed by Catalyst Center, showing advisory severity, CVE identifiers, affected device counts, and available fixed versions — the network security team's starting point for vulnerability management across the managed infrastructure.

## Value

Catalyst Center automatically maps Cisco PSIRTs to your device inventory based on running firmware versions. This UC centralises that mapping in Splunk so the security team can see all active advisories across the fleet in one view, prioritise by severity and blast radius (affected device count), and track which advisories have available fixes. Without this, the security team must log into Catalyst Center's GUI per-advisory — with it, they have a single Pareto table that answers 'what are our biggest vulnerability exposures right now?' and drives the firmware upgrade roadmap.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538). Enable the `securityadvisory` input (Inputs → Create → Security Advisory: account `catcenter-prod`, index `catalyst`, interval `3600`). The TA polls the PSIRT advisory endpoint hourly. Schedule a weekly report for the security operations review.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder running inputs.
- Catalyst Center **2.3.5+** with the Security Advisories feature enabled. This feature automatically maps Cisco PSIRT (Product Security Incident Response Team) publications against your device inventory's firmware versions. Without it, the `securityadvisory` API returns empty responses.
- Service account with **NETWORK-ADMIN-ROLE** (minimum for advisory data).
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Splunk role: security operations users should have a dedicated role (`network_security_analyst`) with `srchIndexesAllowed = catalyst`.
- License headroom: the `securityadvisory` sourcetype generates ~1 event per advisory-device pair per poll × ~700 bytes. A fleet affected by 20 advisories across 200 devices: ~4,000 events/poll × 24 polls/day ≈ 2.7 MB/day. Modest even for large fleets.
- CIM: this sourcetype maps to the **Vulnerabilities** data model. Verify CIM tagging after installation: `| search tag=vulnerability sourcetype="cisco:dnac:securityadvisory"`. If missing, configure tags in the TA's local `tags.conf`.
- Understanding Cisco PSIRT severity levels: CRITICAL (remotely exploitable, no authentication required), HIGH (significant impact with some exploitation constraints), MEDIUM (moderate impact), LOW (minor), INFORMATIONAL (no direct vulnerability). Map these to your organisation's vulnerability management SLAs (e.g., CRITICAL = 72h remediation, HIGH = 30 days).

### Step 1 — Configure data collection
Enable the `securityadvisory` input:

| Setting | Value |
|---------|-------|
| Input type | Security Advisory |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `3600` (hourly — advisory data changes slowly; the Cisco PSIRT publication cadence is weekly/bi-weekly) |

The TA polls `GET /dna/intent/api/v1/security-advisory/advisory`. Catalyst Center maps each advisory against your device inventory based on `softwareVersion` and `platformId`. The response includes advisory metadata (ID, title, severity, CVEs, fixed versions) and the count of affected devices.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" earliest=-2h
| stats dc(advisoryId) as advisories, sum(deviceCount) as total_affected_devices
```
Compare the advisory count with **Catalyst Center > Security Advisories** overview. They should match. If no events arrive, check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" ERROR` — common causes: `401 Unauthorized` (credentials), `403 Forbidden` (insufficient role), `Connection refused` (network).

Expected volume: depends on your fleet's firmware diversity. A fleet running 3 IOS-XE versions across 500 devices typically sees 10–30 advisories with `deviceCount > 0`. A fleet running 15 different versions may see 50+ advisories.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| stats dc(advisoryId) as unique_advisories dc(cveId) as unique_cves sum(deviceCount) as total_affected by severity
| sort case(severity="CRITICAL",1,severity="HIGH",2,severity="MEDIUM",3,severity="LOW",4,1==1,5)
```

Why `dc(advisoryId)` not `count`: the same advisory appears in every poll. `dc(advisoryId)` gives the actual number of distinct active advisories per severity level.

Why `sum(deviceCount)`: shows the total blast radius per severity. `total_affected` for CRITICAL severity answers the executive question: 'how many devices are exposed to critical vulnerabilities right now?'

Why custom `sort` with `case()`: sorts by severity in operational priority order (CRITICAL first) rather than alphabetically. Without this, CRITICAL sorts between "Connected" and "HIGH" — not useful.

For the detailed advisory list (the actionable view for security operations):
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| stats latest(advisoryTitle) as title latest(cveId) as cve latest(deviceCount) as devices latest(fixedVersions) as fixes by advisoryId, severity
| where devices > 0
| sort case(severity="CRITICAL",1,severity="HIGH",2,severity="MEDIUM",3,1==1,4) -devices
```
This produces the Pareto table: highest-severity advisories with the most affected devices at the top. The top row is the single highest-priority vulnerability management action item.

For CIM Vulnerabilities variant (if the data model is accelerated):
```spl
| tstats count from datamodel=Vulnerabilities by Vulnerabilities.severity
```

Schedule as Report: weekly (cron `0 7 * * 1`), output to PDF for the security operations review. For CRITICAL advisories, also schedule daily (cron `0 7 * * *`) — see UC-5.13.35 for real-time alerting.

### Step 3 — Validate
(a) Compare the advisory count and severity distribution with **Catalyst Center > Security Advisories**. The counts should match within one poll cycle.

(b) Pick a specific CRITICAL advisory from the results. Open the Cisco PSIRT portal (`sec.cloudapps.cisco.com`) and verify the advisory ID, severity, and CVE match the Splunk data. Also verify `deviceCount` against the Catalyst Center advisory detail page.

(c) Check for advisories with `deviceCount = 0`: `| where deviceCount = 0 | stats count`. These are advisories that exist in the Cisco PSIRT database but don't affect any device in your fleet (good). The default SPL should focus on `deviceCount > 0` for operational views.

(d) Verify `fixedVersions` is populated: `| where isnotnull(fixedVersions) AND fixedVersions != "[]" | stats count`. If zero, the API may not return fix information — check the Catalyst Center version.

(e) Check CIM mapping: `| tstats count from datamodel=Vulnerabilities by Vulnerabilities.severity`. If no results, the CIM tags need configuration on the Search Head.

(f) Vendor UI parity: open **Catalyst Center > Security Advisories** and compare the severity breakdown chart with the Splunk search results.

### Step 4 — Operationalize
Dashboard (on a "Network Vulnerability Management" dashboard):
- Row 1 — Single value tiles: CRITICAL advisory count (red ≥ 1), HIGH advisory count (orange ≥ 3), total advisories with affected devices.
- Row 2 — Bar chart: advisory count by severity (CRITICAL red, HIGH orange, MEDIUM yellow, LOW grey).
- Row 3 — Detailed advisory table: advisoryId, title, severity, CVE, devices, fixes — sorted by severity and device count. Drilldown: click an advisory → UC-5.13.37 (affected devices).
- Time-picker: fixed to "All time" (advisories are cumulative until remediated).

Runbook (owner: Network Security Operations):
1. Review the weekly advisory report. Focus on CRITICAL and HIGH advisories with `deviceCount > 0`.
2. For each CRITICAL advisory:
   - Check `fixedVersions` — is a patched firmware available?
   - If yes: escalate to the firmware upgrade team (UC-5.13.56). Create an emergency change request if the advisory is actively exploited.
   - If no fix available: check the Cisco PSIRT publication for workarounds (typically ACL changes, feature disablement, or configuration hardening). Apply workarounds immediately for internet-facing devices.
   - Track the advisory through remediation using UC-5.13.38 (Advisory Remediation Progress).
3. For HIGH advisories: assess whether the affected devices are internet-facing, in the CDE (PCI), or in critical infrastructure. Prioritise accordingly. Plan remediation within the SLA window (typically 30 days).
4. For MEDIUM/LOW: include in the next scheduled firmware upgrade campaign. No emergency action required.
5. Generate a monthly vulnerability report for compliance evidence (NIST SI-2 / RA-5). Include: advisory count by severity, affected device count, remediation progress, and open exceptions.

Compliance evidence (NIST SI-2 / RA-5):
- Monthly: export the advisory table as CSV for the vulnerability management evidence folder.
- Quarterly: trend report showing advisory count and affected-device count over time (from UC-5.13.36).
- Annual: comprehensive vulnerability management report including advisory lifecycle (detection → assessment → remediation → closure) for each CRITICAL and HIGH advisory.

### Step 5 — Troubleshooting

- **No advisory events at all** — the `securityadvisory` input is not enabled, or the Catalyst Center doesn't have the Security Advisories feature configured. Check **Catalyst Center > Security Advisories** to verify the feature is available. If the page is empty, Catalyst Center may need to download the advisory database (requires internet connectivity from Catalyst Center to Cisco cloud services).

- **Advisory count in Splunk > Catalyst Center GUI** — the GUI may filter by severity or only show advisories with affected devices by default. The TA may include all advisories including those with `deviceCount=0`. Filter with `| where deviceCount > 0` for the operational view.

- **`deviceCount` is 0 for all advisories** — Catalyst Center hasn't matched advisories to your device inventory. This requires accurate firmware version reporting via device discovery. Check **Catalyst Center > Provision > Inventory** for firmware version accuracy. If versions show as "Unknown," device discovery hasn't completed for those devices.

- **`fixedVersions` is empty or null** — Cisco hasn't released a fix for this advisory yet (zero-day or recently published). Track it for workaround application. Check the Cisco PSIRT publication for interim mitigation guidance.

- **CIM Vulnerabilities model shows no data** — the TA's `tags.conf` may not include the `vulnerability` tag for advisory events. Add it to `$SPLUNK_HOME/etc/apps/TA_cisco_catalyst/local/tags.conf`: `[eventtype=cisco_dnac_advisory]\nvulnerability = enabled`.

- **Same advisory appears multiple times in the table** — the search window covers multiple polls. Use `| stats latest() by advisoryId` to deduplicate.

- **New advisory appears with very high deviceCount** — a newly published CRITICAL PSIRT affecting a common platform (e.g., IOS-XE Web UI vulnerability CVE-2023-20198) can hit hundreds or thousands of devices. This is a genuine security emergency — escalate immediately to the security incident response team.

- **Advisory severity doesn't match the CVE's CVSS score** — Cisco assigns its own severity to PSIRTs based on their product-specific impact assessment, which may differ from the NIST NVD CVSS base score. Use Cisco's severity for operational prioritisation (they know their products best); reference CVSS for compliance reporting if your framework requires it.

- **Want to correlate advisories with firmware compliance** — join with UC-5.13.56 (Firmware Non-Compliance): devices that are both IMAGE non-compliant AND affected by a CRITICAL advisory are the highest-priority targets (they're running old firmware with known vulnerabilities AND not on the golden image).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory"
| stats dc(advisoryId) as unique_advisories dc(cveId) as unique_cves sum(deviceCount) as total_affected by severity
| sort case(severity="CRITICAL",1,severity="HIGH",2,severity="MEDIUM",3,severity="LOW",4,1==1,5)
```

## Visualization

(1) Table: advisoryId, advisoryTitle, severity, cveId, deviceCount, fixedVersions — sorted by severity then deviceCount. (2) Bar chart: advisory count by severity (CRITICAL red, HIGH orange, MEDIUM yellow, LOW grey). (3) Single value: count of CRITICAL/HIGH advisories with affected devices (red ≥ 1). (4) Drilldown to UC-5.13.37 (affected devices per advisory) for remediation targeting.

## Known False Positives

**Same advisory re-polled on every cycle inflating the event count.** The securityadvisory API returns all current advisories on each poll. If you count events rather than distinct `advisoryId` values, counts inflate with each poll cycle. Distinguish by checking whether `| stats dc(advisoryId)` is significantly lower than `| stats count`. Suppress by using `dc(advisoryId)` for advisory metrics instead of event count.

**INFORMATIONAL severity advisories with zero affected devices.** Catalyst Center may include INFORMATIONAL advisories in the feed that do not affect any devices in the managed inventory. These can inflate the total advisory count. Distinguish by checking `deviceCount` — if 0, the advisory is informational only. Suppress by filtering `| where deviceCount>0` for operationally relevant advisory dashboards.

**Advisory impact classification still in progress.** When Catalyst Center first detects a new PSIRT advisory, it may still be classifying the impact (which devices are affected, which versions are vulnerable). During this period, the advisory appears with incomplete data. Distinguish by checking whether `deviceCount` is null or changes between polls. Suppress by allowing 24 hours after a new advisory's `first_seen` before including it in operational dashboards.

**Catalyst Center PSIRT database update re-scanning and surfacing previously cleared advisories.** When Catalyst Center updates its PSIRT database, it re-scans the inventory and may re-detect advisories that were previously assessed and accepted. Distinguish by checking whether the advisory's `advisoryId` appeared in earlier data with a resolution status. Suppress by maintaining a `catalyst_advisory_exceptions` lookup for risk-accepted advisories.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](../../docs/guides/catalyst-center.md)
- [Cisco PSIRT Security Advisories](https://sec.cloudapps.cisco.com/security/center/publicationListing.x)
