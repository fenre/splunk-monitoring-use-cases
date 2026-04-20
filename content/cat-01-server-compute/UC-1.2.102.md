---
id: "1.2.102"
title: "Software Restriction / AppLocker Bypass Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.102 · Software Restriction / AppLocker Bypass Detection

## Description

Application whitelisting is a primary defense against malware. Detecting bypass attempts reveals both sophisticated attackers and policy gaps.

## Value

Application whitelisting is a primary defense against malware. Detecting bypass attempts reveals both sophisticated attackers and policy gaps.

## Implementation

Collect all four AppLocker log channels (EXE/DLL, MSI/Script, Packaged app, Script). Track blocked executions (8004/8007/8022/8025) and audit-mode warnings (8003/8006). Alert on repeated blocks from same user (attempted bypass), blocks in admin paths, and execution of known LOLBins that bypass default rules (mshta.exe, regsvr32.exe, msbuild.exe). Correlate with Sysmon for parent process context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL`, `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/MSI and Script`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect all four AppLocker log channels (EXE/DLL, MSI/Script, Packaged app, Script). Track blocked executions (8004/8007/8022/8025) and audit-mode warnings (8003/8006). Alert on repeated blocks from same user (attempted bypass), blocks in admin paths, and execution of known LOLBins that bypass default rules (mshta.exe, regsvr32.exe, msbuild.exe). Correlate with Sysmon for parent process context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007, 8022, 8025)
| eval BlockType=case(EventCode=8004,"EXE_Blocked", EventCode=8007,"Script_Blocked", EventCode=8022,"MSI_Blocked", EventCode=8025,"DLL_Blocked", 1=1,"Other")
| stats count by host, UserName, BlockType, RuleName, FilePath
| sort -count
```

Understanding this SPL

**Software Restriction / AppLocker Bypass Detection** — Application whitelisting is a primary defense against malware. Detecting bypass attempts reveals both sophisticated attackers and policy gaps.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/EXE and DLL`, `sourcetype=WinEventLog:Microsoft-Windows-AppLocker/MSI and Script`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **BlockType** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, UserName, BlockType, RuleName, FilePath** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (blocks by type), Table (blocked files), Timechart (block trends).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-AppLocker*" EventCode IN (8004, 8007, 8022, 8025)
| eval BlockType=case(EventCode=8004,"EXE_Blocked", EventCode=8007,"Script_Blocked", EventCode=8022,"MSI_Blocked", EventCode=8025,"DLL_Blocked", 1=1,"Other")
| stats count by host, UserName, BlockType, RuleName, FilePath
| sort -count
```

## Visualization

Bar chart (blocks by type), Table (blocked files), Timechart (block trends).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
