---
id: "1.2.114"
title: "LSASS Memory Protection Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.114 · LSASS Memory Protection Monitoring

## Description

LSASS contains credentials in memory. Monitoring LSASS access attempts and protection status detects credential dumping tools like Mimikatz.

## Value

LSASS contains credentials in memory. Monitoring LSASS access attempts and protection status detects credential dumping tools like Mimikatz.

## Implementation

Sysmon EventCode 10 (ProcessAccess) targeting lsass.exe. Filter legitimate AV/EDR processes. Focus on suspicious access masks: 0x1010 (PROCESS_QUERY_LIMITED_INFORMATION + PROCESS_VM_READ), 0x1FFFFF (PROCESS_ALL_ACCESS), 0x143A (used by Mimikatz sekurlsa). Enable RunAsPPL for LSASS protection and monitor for its status. Alert on any non-whitelisted LSASS access. MITRE ATT&CK T1003.001.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10), `sourcetype=WinEventLog:Security`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCode 10 (ProcessAccess) targeting lsass.exe. Filter legitimate AV/EDR processes. Focus on suspicious access masks: 0x1010 (PROCESS_QUERY_LIMITED_INFORMATION + PROCESS_VM_READ), 0x1FFFFF (PROCESS_ALL_ACCESS), 0x143A (used by Mimikatz sekurlsa). Enable RunAsPPL for LSASS protection and monitor for its status. Alert on any non-whitelisted LSASS access. MITRE ATT&CK T1003.001.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=10 TargetImage="*\\lsass.exe"
| where NOT match(SourceImage, "(?i)(csrss|services|svchost|wininit|MsMpEng|MsSense|CrowdStrike|SentinelAgent)")
| eval GrantedAccess_hex=GrantedAccess
| table _time, host, SourceImage, SourceUser, GrantedAccess_hex, CallTrace
| where match(GrantedAccess_hex, "0x1010|0x1FFFFF|0x143A")
| sort -_time
```

Understanding this SPL

**LSASS Memory Protection Monitoring** — LSASS contains credentials in memory. Monitoring LSASS access attempts and protection status detects credential dumping tools like Mimikatz.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 10), `sourcetype=WinEventLog:Security`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(SourceImage, "(?i)(csrss|services|svchost|wininit|MsMpEng|MsSense|CrowdStrike|SentinelAgent)")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **GrantedAccess_hex** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **LSASS Memory Protection Monitoring**): table _time, host, SourceImage, SourceUser, GrantedAccess_hex, CallTrace
• Filters the current rows with `where match(GrantedAccess_hex, "0x1010|0x1FFFFF|0x143A")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (access events), Alert on suspicious access masks, Single value (LSASS PPL status).

## SPL

```spl
index=wineventlog EventCode=10 TargetImage="*\\lsass.exe"
| where NOT match(SourceImage, "(?i)(csrss|services|svchost|wininit|MsMpEng|MsSense|CrowdStrike|SentinelAgent)")
| eval GrantedAccess_hex=GrantedAccess
| table _time, host, SourceImage, SourceUser, GrantedAccess_hex, CallTrace
| where match(GrantedAccess_hex, "0x1010|0x1FFFFF|0x143A")
| sort -_time
```

## Visualization

Table (access events), Alert on suspicious access masks, Single value (LSASS PPL status).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
