---
id: "1.2.113"
title: "COM Object Hijacking Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.113 · COM Object Hijacking Detection

## Description

COM hijacking replaces legitimate COM objects with malicious ones for persistence and privilege escalation. It's a stealthy technique that survives reboots.

## Value

COM hijacking replaces legitimate COM objects with malicious ones for persistence and privilege escalation. It's a stealthy technique that survives reboots.

## Implementation

Monitor Sysmon registry value set events (EventCode 13) targeting CLSID InprocServer32 and LocalServer32 keys in HKCU and HKLM. Filter out legitimate installers (msiexec, TrustedInstaller). Alert on modifications pointing to unusual DLL paths (temp directories, user profiles, AppData). Maintain baseline of known-good CLSID registrations. MITRE ATT&CK T1546.015.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor Sysmon registry value set events (EventCode 13) targeting CLSID InprocServer32 and LocalServer32 keys in HKCU and HKLM. Filter out legitimate installers (msiexec, TrustedInstaller). Alert on modifications pointing to unusual DLL paths (temp directories, user profiles, AppData). Maintain baseline of known-good CLSID registrations. MITRE ATT&CK T1546.015.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=13 TargetObject="*\\Classes\\CLSID\\*\\InprocServer32*"
| where NOT match(Image, "(?i)(msiexec|svchost|TiWorker|TrustedInstaller|DismHost)")
| table _time, host, User, Image, TargetObject, Details
| rex field=TargetObject "CLSID\\\\(?<CLSID>[^\\\\]+)"
| sort -_time
```

Understanding this SPL

**COM Object Hijacking Detection** — COM hijacking replaces legitimate COM objects with malicious ones for persistence and privilege escalation. It's a stealthy technique that survives reboots.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 13). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(Image, "(?i)(msiexec|svchost|TiWorker|TrustedInstaller|DismHost)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **COM Object Hijacking Detection**): table _time, host, User, Image, TargetObject, Details
• Extracts fields with `rex` (regular expression).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (registry changes), Alert on suspicious CLSID modifications.

## SPL

```spl
index=wineventlog EventCode=13 TargetObject="*\\Classes\\CLSID\\*\\InprocServer32*"
| where NOT match(Image, "(?i)(msiexec|svchost|TiWorker|TrustedInstaller|DismHost)")
| table _time, host, User, Image, TargetObject, Details
| rex field=TargetObject "CLSID\\\\(?<CLSID>[^\\\\]+)"
| sort -_time
```

## Visualization

Table (registry changes), Alert on suspicious CLSID modifications.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
