---
id: "1.2.68"
title: "NTFS Corruption and Self-Healing"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.68 · NTFS Corruption and Self-Healing

## Description

NTFS corruption can cause data loss, application failures, and boot issues. Self-healing events indicate disk degradation that will worsen.

## Value

NTFS corruption can cause data loss, application failures, and boot issues. Self-healing events indicate disk degradation that will worsen.

## Implementation

NTFS events log automatically. EventCode 55=structure corruption on volume (critical), 98=volume marked dirty (chkdsk needed at boot), 137/140=self-healing activity. Any EventCode 55 requires immediate attention — indicates metadata corruption that may spread. Correlate with WHEA (hardware) and SMART events to determine if underlying disk is failing. Schedule chkdsk offline and plan disk replacement.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Source=Ntfs, EventCode 55, 98, 137, 140).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
NTFS events log automatically. EventCode 55=structure corruption on volume (critical), 98=volume marked dirty (chkdsk needed at boot), 137/140=self-healing activity. Any EventCode 55 requires immediate attention — indicates metadata corruption that may spread. Correlate with WHEA (hardware) and SMART events to determine if underlying disk is failing. Schedule chkdsk offline and plan disk replacement.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Ntfs" EventCode IN (55, 98, 137, 140)
| eval issue=case(EventCode=55,"NTFS corruption detected",EventCode=98,"Volume dirty flag set",EventCode=137,"Self-healing started",EventCode=140,"Self-healing completed")
| table _time, host, issue, DriveName, CorruptionType
| sort -_time
```

Understanding this SPL

**NTFS Corruption and Self-Healing** — NTFS corruption can cause data loss, application failures, and boot issues. Self-healing events indicate disk degradation that will worsen.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Ntfs, EventCode 55, 98, 137, 140). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **NTFS Corruption and Self-Healing**): table _time, host, issue, DriveName, CorruptionType
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (corruption events), Timeline, Single value (affected volumes — target: 0).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Ntfs" EventCode IN (55, 98, 137, 140)
| eval issue=case(EventCode=55,"NTFS corruption detected",EventCode=98,"Volume dirty flag set",EventCode=137,"Self-healing started",EventCode=140,"Self-healing completed")
| table _time, host, issue, DriveName, CorruptionType
| sort -_time
```

## Visualization

Table (corruption events), Timeline, Single value (affected volumes — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
