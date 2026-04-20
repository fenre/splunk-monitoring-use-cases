---
id: "1.2.110"
title: "PowerShell Constrained Language Mode Bypass"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.110 · PowerShell Constrained Language Mode Bypass

## Description

Constrained Language Mode limits PowerShell attack surface. Detecting bypasses reveals attackers escalating from restricted to full-language mode for malware execution.

## Value

Constrained Language Mode limits PowerShell attack surface. Detecting bypasses reveals attackers escalating from restricted to full-language mode for malware execution.

## Implementation

Enable PowerShell Script Block Logging (EventCode 4104) and Module Logging. Search for scripts that attempt to change LanguageMode, use reflection to bypass CLM, or reference FullLanguage mode. Alert on Add-Type with DllImport (P/Invoke) in constrained environments — this is a common CLM bypass. Correlate with AppLocker and WDAC logs for defense-in-depth monitoring.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104), `sourcetype=WinEventLog:Windows PowerShell`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable PowerShell Script Block Logging (EventCode 4104) and Module Logging. Search for scripts that attempt to change LanguageMode, use reflection to bypass CLM, or reference FullLanguage mode. Alert on Add-Type with DllImport (P/Invoke) in constrained environments — this is a common CLM bypass. Correlate with AppLocker and WDAC logs for defense-in-depth monitoring.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=4104
| where match(ScriptBlockText, "(?i)(FullLanguage|LanguageMode|Add-Type.*DllImport|System\.Management\.Automation\.LanguageMode)")
| table _time, host, UserName, ScriptBlockText, Path
| sort -_time
```

Understanding this SPL

**PowerShell Constrained Language Mode Bypass** — Constrained Language Mode limits PowerShell attack surface. Detecting bypasses reveals attackers escalating from restricted to full-language mode for malware execution.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-PowerShell/Operational` (EventCode 4104), `sourcetype=WinEventLog:Windows PowerShell`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where match(ScriptBlockText, "(?i)(FullLanguage|LanguageMode|Add-Type.*DllImport|System\.Management\.Automation\.LanguageMo…` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **PowerShell Constrained Language Mode Bypass**): table _time, host, UserName, ScriptBlockText, Path
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (bypass attempts), Alert on detection, Single value (count).

## SPL

```spl
index=wineventlog EventCode=4104
| where match(ScriptBlockText, "(?i)(FullLanguage|LanguageMode|Add-Type.*DllImport|System\.Management\.Automation\.LanguageMode)")
| table _time, host, UserName, ScriptBlockText, Path
| sort -_time
```

## Visualization

Table (bypass attempts), Alert on detection, Single value (count).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
