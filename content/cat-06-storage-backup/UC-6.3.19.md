<!-- AUTO-GENERATED from UC-6.3.19.json — DO NOT EDIT -->

---
id: "6.3.19"
title: "Windows Backup Job Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.3.19 · Windows Backup Job Monitoring

## Description

Windows Server Backup failures mean the server has no recovery point. Silent failures create a false sense of protection.

## Value

Windows Server Backup failures mean the server has no recovery point. Silent failures create a false sense of protection.

## Implementation

Forward Windows Backup event logs. EventCode 4=success, 5=failure, 8=VSS failure. Alert on any backup failure (EventCode 5, 8). Also monitor for missing backups — if a server stops reporting EventCode 4, the backup job may have been disabled or deleted. Compare actual backup frequency against RTO/RPO requirements. Escalate servers with no successful backup in 48+ hours.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Backup` (EventCode 4, 5, 8, 9, 14, 17, 22).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Windows Backup event logs. EventCode 4=success, 5=failure, 8=VSS failure. Alert on any backup failure (EventCode 5, 8). Also monitor for missing backups — if a server stops reporting EventCode 4, the backup job may have been disabled or deleted. Compare actual backup frequency against RTO/RPO requirements. Escalate servers with no successful backup in 48+ hours.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Backup"
  EventCode IN (4, 5, 8, 9, 14)
| eval status=case(EventCode=4,"Backup completed",EventCode=5,"Backup failed",EventCode=8,"Backup failed (VSS)",EventCode=9,"Warning",EventCode=14,"Backup completed with warnings")
| table _time, host, status, EventCode, BackupTarget
| sort -_time
```

Understanding this SPL

**Windows Backup Job Monitoring** — Windows Server Backup failures mean the server has no recovery point. Silent failures create a false sense of protection.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Backup` (EventCode 4, 5, 8, 9, 14, 17, 22). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Windows Backup Job Monitoring**): table _time, host, status, EventCode, BackupTarget
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same metric, object name, and interval in the vendor or cloud console (array, backup, or object store) that is the source of truth for this feed.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. List media server, proxy, and repository names in the runbook, and when to open a ticket with the application team versus the backup team. Consider visualizations: Status grid (host × backup status), Table (failures), Line chart (backup success rate over time), Single value (hours since last backup).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Backup"
  EventCode IN (4, 5, 8, 9, 14)
| eval status=case(EventCode=4,"Backup completed",EventCode=5,"Backup failed",EventCode=8,"Backup failed (VSS)",EventCode=9,"Warning",EventCode=14,"Backup completed with warnings")
| table _time, host, status, EventCode, BackupTarget
| sort -_time
```

## Visualization

Status grid (host × backup status), Table (failures), Line chart (backup success rate over time), Single value (hours since last backup).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
