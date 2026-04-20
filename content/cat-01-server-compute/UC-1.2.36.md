---
id: "1.2.36"
title: "DCSync Attack Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.36 · DCSync Attack Detection

## Description

DCSync uses Directory Replication Service permissions to extract password hashes remotely. Detecting non-DC replication requests catches this attack before credential theft completes.

## Value

DCSync uses Directory Replication Service permissions to extract password hashes remotely. Detecting non-DC replication requests catches this attack before credential theft completes.

## Implementation

Enable Directory Service Access auditing on domain controllers. EventCode 4662 with GUID 1131f6aa (DS-Replication-Get-Changes) or 1131f6ad (DS-Replication-Get-Changes-All) from a non-machine account (not ending in $) is a DCSync indicator. Alert immediately with critical priority. Legitimate replication only occurs between DCs (machine accounts). MITRE ATT&CK T1003.006.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4662).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Directory Service Access auditing on domain controllers. EventCode 4662 with GUID 1131f6aa (DS-Replication-Get-Changes) or 1131f6ad (DS-Replication-Get-Changes-All) from a non-machine account (not ending in $) is a DCSync indicator. Alert immediately with critical priority. Legitimate replication only occurs between DCs (machine accounts). MITRE ATT&CK T1003.006.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4662
  AccessMask="0x100"
  (Properties="*1131f6aa*" OR Properties="*1131f6ad*" OR Properties="*89e95b76*")
| where NOT match(SubjectUserName, "(?i)(\\$$)")
| table _time, host, SubjectUserName, SubjectDomainName, ObjectName
| sort -_time
```

Understanding this SPL

**DCSync Attack Detection** — DCSync uses Directory Replication Service permissions to extract password hashes remotely. Detecting non-DC replication requests catches this attack before credential theft completes.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4662). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where NOT match(SubjectUserName, "(?i)(\\$$)")` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **DCSync Attack Detection**): table _time, host, SubjectUserName, SubjectDomainName, ObjectName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (replication requests from non-DCs), Single value (count — target: 0), Alert with analyst playbook.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4662
  AccessMask="0x100"
  (Properties="*1131f6aa*" OR Properties="*1131f6ad*" OR Properties="*89e95b76*")
| where NOT match(SubjectUserName, "(?i)(\\$$)")
| table _time, host, SubjectUserName, SubjectDomainName, ObjectName
| sort -_time
```

## Visualization

Table (replication requests from non-DCs), Single value (count — target: 0), Alert with analyst playbook.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
