<!-- AUTO-GENERATED from UC-1.2.97.json — DO NOT EDIT -->

---
id: "1.2.97"
title: "Print Spooler Vulnerability Monitoring (PrintNightmare)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.97 · Print Spooler Vulnerability Monitoring (PrintNightmare)

## Description

Print Spooler vulnerabilities (CVE-2021-34527, CVE-2021-1675) enable remote code execution and privilege escalation. Continuous monitoring ensures patches hold and exploitation attempts are caught.

## Value

The print spooler keeps showing up in critical security patches. Driver installs, new printers, and odd RPC to spooler remain key signals of repeat exploitation and misconfigurations.

## Implementation

Audit Print Service Operational log for driver installations (316), and Sysmon for DLL drops into spool\drivers directory (EventCode 11). On non-print servers, the Print Spooler service should be disabled — alert if running. On print servers, monitor for unsigned driver installations and remote driver additions. Alert on any spoolsv.exe spawning cmd.exe or powershell.exe.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`, `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Audit Print Service Operational log for driver installations (316), and Sysmon for DLL drops into spool\drivers directory (EventCode 11). On non-print servers, the Print Spooler service should be disabled — alert if running. On print servers, monitor for unsigned driver installations and remote driver additions. Alert on any spoolsv.exe spawning cmd.exe or powershell.exe.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog ((source="WinEventLog:Microsoft-Windows-PrintService/Operational" EventCode IN (316, 808, 811))
  OR (EventCode=11 TargetFilename="*\\spool\\drivers\\*"))
| eval Indicator=case(EventCode=316,"Driver_Install", EventCode=808,"RestrictDriverInstallation", EventCode=11,"Driver_File_Drop", 1=1,"Other")
| table _time, host, Indicator, UserName, DriverName, TargetFilename
| sort -_time
```

Understanding this SPL

**Print Spooler Vulnerability Monitoring (PrintNightmare)** — Print Spooler vulnerabilities (CVE-2021-34527, CVE-2021-1675) enable remote code execution and privilege escalation. Continuous monitoring ensures patches hold and exploitation attempts are caught.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-PrintService/Operational`, `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Indicator** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Print Spooler Vulnerability Monitoring (PrintNightmare)**): table _time, host, Indicator, UserName, DriverName, TargetFilename
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (events), Single value (spooler running on non-print servers), Alert on exploitation indicators.

## SPL

```spl
index=wineventlog ((source="WinEventLog:Microsoft-Windows-PrintService/Operational" EventCode IN (316, 808, 811))
  OR (EventCode=11 TargetFilename="*\\spool\\drivers\\*"))
| eval Indicator=case(EventCode=316,"Driver_Install", EventCode=808,"RestrictDriverInstallation", EventCode=11,"Driver_File_Drop", 1=1,"Other")
| table _time, host, Indicator, UserName, DriverName, TargetFilename
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Processes
  by Processes.user Processes.dest span=1h
| where count > 0
```

## Visualization

Table (events), Single value (spooler running on non-print servers), Alert on exploitation indicators.

## References

- [Audit Print Service Operational log for driver installations](https://splunkbase.splunk.com/app/316)
- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
