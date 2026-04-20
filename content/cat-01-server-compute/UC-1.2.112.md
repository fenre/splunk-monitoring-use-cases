---
id: "1.2.112"
title: "BITS Transfer Abuse Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.112 · BITS Transfer Abuse Detection

## Description

Background Intelligent Transfer Service (BITS) is abused by malware for stealthy downloads and persistence. Monitoring BITS jobs detects LOLBin-based attacks.

## Value

Background Intelligent Transfer Service (BITS) is abused by malware for stealthy downloads and persistence. Monitoring BITS jobs detects LOLBin-based attacks.

## Implementation

Enable BITS Client Operational logging. Track job creation (59), modification (60), and completion (3/61). Filter out legitimate BITS usage (Windows Update, Edge updates). Alert on BITS jobs downloading from unusual URLs, jobs created by unexpected processes (not svchost or system), and BITS persistence via /SetNotifyCmdLine. MITRE ATT&CK T1197.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Bits-Client/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable BITS Client Operational logging. Track job creation (59), modification (60), and completion (3/61). Filter out legitimate BITS usage (Windows Update, Edge updates). Alert on BITS jobs downloading from unusual URLs, jobs created by unexpected processes (not svchost or system), and BITS persistence via /SetNotifyCmdLine. MITRE ATT&CK T1197.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Bits-Client/Operational" EventCode IN (3, 4, 59, 60, 61)
| eval Status=case(EventCode=3,"Transfer_Complete", EventCode=4,"Transfer_Cancelled", EventCode=59,"Job_Created", EventCode=60,"Job_Modified", EventCode=61,"Job_Transferred", 1=1,"Other")
| table _time, host, User, jobTitle, url, fileList, Status, bytesTransferred
| where NOT match(url, "(?i)(windowsupdate|microsoft\.com|msedge)")
| sort -_time
```

Understanding this SPL

**BITS Transfer Abuse Detection** — Background Intelligent Transfer Service (BITS) is abused by malware for stealthy downloads and persistence. Monitoring BITS jobs detects LOLBin-based attacks.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Bits-Client/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **BITS Transfer Abuse Detection**): table _time, host, User, jobTitle, url, fileList, Status, bytesTransferred
• Filters the current rows with `where NOT match(url, "(?i)(windowsupdate|microsoft\.com|msedge)")` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (BITS jobs), Timechart (transfer volume), Alert on non-standard URLs.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Bits-Client/Operational" EventCode IN (3, 4, 59, 60, 61)
| eval Status=case(EventCode=3,"Transfer_Complete", EventCode=4,"Transfer_Cancelled", EventCode=59,"Job_Created", EventCode=60,"Job_Modified", EventCode=61,"Job_Transferred", 1=1,"Other")
| table _time, host, User, jobTitle, url, fileList, Status, bytesTransferred
| where NOT match(url, "(?i)(windowsupdate|microsoft\.com|msedge)")
| sort -_time
```

## Visualization

Table (BITS jobs), Timechart (transfer volume), Alert on non-standard URLs.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
