---
id: "1.2.48"
title: "PowerShell Script Block Logging"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.48 · PowerShell Script Block Logging

## Description

Script Block Logging captures the full text of every PowerShell script executed, including deobfuscated code. Essential for detecting fileless attacks and encoded commands.

## Value

Script Block Logging captures the full text of every PowerShell script executed, including deobfuscated code. Essential for detecting fileless attacks and encoded commands.

## Implementation

Enable Script Block Logging via GPO: Computer Configuration → Administrative Templates → Windows PowerShell → Turn on PowerShell Script Block Logging. EventCode 4104 logs the full script text, including auto-deobfuscation. Search for suspicious keywords: `Invoke-Expression`, `Net.WebClient`, `DownloadString`, `FromBase64String`, `Invoke-Mimikatz`. High volume — consider targeted alerting and summary indexing. Complements EventCode 4688 (process creation with command line).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Script Block Logging via GPO: Computer Configuration → Administrative Templates → Windows PowerShell → Turn on PowerShell Script Block Logging. EventCode 4104 logs the full script text, including auto-deobfuscation. Search for suspicious keywords: `Invoke-Expression`, `Net.WebClient`, `DownloadString`, `FromBase64String`, `Invoke-Mimikatz`. High volume — consider targeted alerting and summary indexing. Complements EventCode 4688 (process creation with command line).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText IN ("*Invoke-Mimikatz*","*Net.WebClient*","*DownloadString*","*IEX*","*-enc*","*FromBase64*","*Invoke-Expression*")
| table _time, host, Path, ScriptBlockText, UserName
| sort -_time
```

Understanding this SPL

**PowerShell Script Block Logging** — Script Block Logging captures the full text of every PowerShell script executed, including deobfuscated code. Essential for detecting fileless attacks and encoded commands.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-PowerShell/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **PowerShell Script Block Logging**): table _time, host, Path, ScriptBlockText, UserName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious scripts), Timeline, Bar chart (script execution by host), Search interface for threat hunting.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText IN ("*Invoke-Mimikatz*","*Net.WebClient*","*DownloadString*","*IEX*","*-enc*","*FromBase64*","*Invoke-Expression*")
| table _time, host, Path, ScriptBlockText, UserName
| sort -_time
```

## Visualization

Table (suspicious scripts), Timeline, Bar chart (script execution by host), Search interface for threat hunting.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
