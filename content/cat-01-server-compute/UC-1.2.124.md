<!-- AUTO-GENERATED from UC-1.2.124.json — DO NOT EDIT -->

---
id: "1.2.124"
title: "Process Injection Detection (Sysmon)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.124 · Process Injection Detection (Sysmon)

## Description

Process injection hides malicious code inside legitimate processes. Detecting injection techniques (CreateRemoteThread, APC, process hollowing) catches advanced malware.

## Value

Process injection is a core defense-evasion technique. Sysmon-class telemetry on create remote thread and similar gives IR a process tree when EDR is not everywhere.

## Implementation

Sysmon EventCode 8 (CreateRemoteThread) detects thread injection into remote processes. Filter legitimate EDR/AV injections. EventCode 10 (ProcessAccess) with specific access masks (0x1FFFFF=ALL_ACCESS, 0x801=VM_WRITE+QUERY) detects memory writes for process hollowing. Alert on any remote thread creation targeting system processes (explorer.exe, svchost.exe, services.exe). Correlate with EventCode 1 for full process chain. MITRE ATT&CK T1055.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 8, 10).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Sysmon EventCode 8 (CreateRemoteThread) detects thread injection into remote processes. Filter legitimate EDR/AV injections. EventCode 10 (ProcessAccess) with specific access masks (0x1FFFFF=ALL_ACCESS, 0x801=VM_WRITE+QUERY) detects memory writes for process hollowing. Alert on any remote thread creation targeting system processes (explorer.exe, svchost.exe, services.exe). Correlate with EventCode 1 for full process chain. MITRE ATT&CK T1055.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=8
| where NOT match(SourceImage, "(?i)(csrss|MsMpEng|SentinelAgent|CrowdStrike)")
| eval InjectionTarget=TargetImage
| table _time, host, SourceImage, InjectionTarget, SourceUser, StartModule, StartFunction
| append [search index=wineventlog EventCode=10 GrantedAccess IN ("0x1FFFFF","0x801","0x1FFB") | where NOT match(SourceImage, "(?i)(csrss|MsMpEng|lsass)") | table _time, host, SourceImage, TargetImage, SourceUser, GrantedAccess]
| sort -_time
```

Understanding this SPL

**Process Injection Detection (Sysmon)** — Process injection hides malicious code inside legitimate processes. Detecting injection techniques (CreateRemoteThread, APC, process hollowing) catches advanced malware.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 8, 10). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(SourceImage, "(?i)(csrss|MsMpEng|SentinelAgent|CrowdStrike)")` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **InjectionTarget** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Process Injection Detection (Sysmon)**): table _time, host, SourceImage, InjectionTarget, SourceUser, StartModule, StartFunction
• Appends rows from a subsearch with `append`.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (injection events), Network diagram (source→target), Alert on detection.

## SPL

```spl
index=wineventlog EventCode=8
| where NOT match(SourceImage, "(?i)(csrss|MsMpEng|SentinelAgent|CrowdStrike)")
| eval InjectionTarget=TargetImage
| table _time, host, SourceImage, InjectionTarget, SourceUser, StartModule, StartFunction
| append [search index=wineventlog EventCode=10 GrantedAccess IN ("0x1FFFFF","0x801","0x1FFB") | where NOT match(SourceImage, "(?i)(csrss|MsMpEng|lsass)") | table _time, host, SourceImage, TargetImage, SourceUser, GrantedAccess]
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.user Processes.parent_process_name Processes.dest span=1h
| where count > 0
```

## Visualization

Table (injection events), Network diagram (source→target), Alert on detection.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
