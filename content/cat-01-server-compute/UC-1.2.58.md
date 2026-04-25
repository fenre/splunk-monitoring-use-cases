<!-- AUTO-GENERATED from UC-1.2.58.json — DO NOT EDIT -->

---
id: "1.2.58"
title: "Storage Spaces Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.58 · Storage Spaces Health Monitoring

## Description

Storage Spaces pools degrade silently when physical disks fail. Detection before a second disk fails prevents data loss in mirrored/parity configurations.

## Value

For software-only RAID, *your* observability is the only early warning the SAN team used to have with their own lights—do not under-alert here.

## Implementation

Storage Spaces driver events log automatically. Monitor for pool degradation (lost redundancy) and disk failures. Alert at critical priority on any degradation — the pool is now running without full redundancy. Track repair progress (EventCode 207). Also poll via PowerShell scripted input: `Get-StoragePool | Get-PhysicalDisk | Where OperationalStatus -ne 'OK'` for proactive monitoring beyond event-based detection.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-StorageSpaces-Driver/Operational` (EventCode 1, 2, 3, 207).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Storage Spaces driver events log automatically. Monitor for pool degradation (lost redundancy) and disk failures. Alert at critical priority on any degradation — the pool is now running without full redundancy. Track repair progress (EventCode 207). Also poll via PowerShell scripted input: `Get-StoragePool | Get-PhysicalDisk | Where OperationalStatus -ne 'OK'` for proactive monitoring beyond event-based detection.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-StorageSpaces*" EventCode IN (1, 2, 3, 207)
| eval status=case(EventCode=1,"Pool degraded",EventCode=2,"Disk failed",EventCode=3,"IO error",EventCode=207,"Repair started")
| table _time, host, status, PhysicalDiskId, PoolName
| sort -_time
```

Understanding this SPL

**Storage Spaces Health Monitoring** — Storage Spaces pools degrade silently when physical disks fail. Detection before a second disk fails prevents data loss in mirrored/parity configurations.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-StorageSpaces-Driver/Operational` (EventCode 1, 2, 3, 207). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Storage Spaces Health Monitoring**): table _time, host, status, PhysicalDiskId, PoolName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (pool × disk health), Timeline (degradation events), Single value (degraded pools — target: 0).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-StorageSpaces*" EventCode IN (1, 2, 3, 207)
| eval status=case(EventCode=1,"Pool degraded",EventCode=2,"Disk failed",EventCode=3,"IO error",EventCode=207,"Repair started")
| table _time, host, status, PhysicalDiskId, PoolName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action span=1h
| where count>0
```

## Visualization

Status grid (pool × disk health), Timeline (degradation events), Single value (degraded pools — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
