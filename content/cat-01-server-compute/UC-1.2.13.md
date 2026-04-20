---
id: "1.2.13"
title: "PowerShell Script Execution"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.13 · PowerShell Script Execution

## Description

PowerShell is the most common tool in modern Windows attacks (Cobalt Strike, Empire, fileless malware). Script block logging captures the actual code executed.

## Value

PowerShell is the most common tool in modern Windows attacks (Cobalt Strike, Empire, fileless malware). Script block logging captures the actual code executed.

## Implementation

Enable PowerShell Script Block Logging via GPO: `Administrative Templates > Windows Components > Windows PowerShell > Turn on PowerShell Script Block Logging`. Forward the PowerShell Operational log. Create alerts on suspicious keywords (encoded commands, invoke-expression, web client downloads).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational`, EventCode=4104.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable PowerShell Script Block Logging via GPO: `Administrative Templates > Windows Components > Windows PowerShell > Turn on PowerShell Script Block Logging`. Forward the PowerShell Operational log. Create alerts on suspicious keywords (encoded commands, invoke-expression, web client downloads).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText="*EncodedCommand*" OR ScriptBlockText="*Invoke-Mimikatz*" OR ScriptBlockText="*Net.WebClient*" OR ScriptBlockText="*-nop -w hidden*"
| table _time host ScriptBlockText
| sort -_time
```

Understanding this SPL

**PowerShell Script Execution** — PowerShell is the most common tool in modern Windows attacks (Cobalt Strike, Empire, fileless malware). Script block logging captures the actual code executed.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational`, EventCode=4104. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-PowerShell/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **PowerShell Script Execution**): table _time host ScriptBlockText
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Events list (full script block text), Table of suspicious commands, Volume timechart.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-PowerShell/Operational" EventCode=4104
| search ScriptBlockText="*EncodedCommand*" OR ScriptBlockText="*Invoke-Mimikatz*" OR ScriptBlockText="*Net.WebClient*" OR ScriptBlockText="*-nop -w hidden*"
| table _time host ScriptBlockText
| sort -_time
```

## Visualization

Events list (full script block text), Table of suspicious commands, Volume timechart.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
