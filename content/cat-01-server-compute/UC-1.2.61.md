<!-- AUTO-GENERATED from UC-1.2.61.json — DO NOT EDIT -->

---
id: "1.2.61"
title: "Data Deduplication Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.61 · Data Deduplication Health

## Description

Windows Data Deduplication saves significant storage on file servers. Job failures or savings degradation indicate volume corruption or configuration issues.

## Value

Deduplication and backup are the same RPO story in many shops—if dedupe is sick, *effective* free space and restore paths are at risk, not a math row in a spreadsheet only.

## Implementation

Enable Deduplication Operational log on file servers with dedup enabled. EventCode 6155=optimization job failure, 12802=data corruption detected. Monitor savings rate trending — declining rates suggest changing data patterns or dedup overhead. Alert on any corruption detection (12802) immediately. Track optimization duration — increasing times indicate volume growth outpacing dedup capacity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Deduplication/Operational` (EventCode 6153, 6155, 12800, 12802).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Deduplication Operational log on file servers with dedup enabled. EventCode 6155=optimization job failure, 12802=data corruption detected. Monitor savings rate trending — declining rates suggest changing data patterns or dedup overhead. Alert on any corruption detection (12802) immediately. Track optimization duration — increasing times indicate volume growth outpacing dedup capacity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Deduplication*"
  EventCode IN (6153, 6155, 12800, 12802)
| eval status=case(EventCode=6153,"Optimization completed",EventCode=6155,"Optimization failed",EventCode=12800,"Scrubbing completed",EventCode=12802,"Corruption detected")
| table _time, host, status, VolumeName, SavingsRate, CorruptionCount
| sort -_time
```

Understanding this SPL

**Data Deduplication Health** — Windows Data Deduplication saves significant storage on file servers. Job failures or savings degradation indicate volume corruption or configuration issues.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Deduplication/Operational` (EventCode 6153, 6155, 12800, 12802). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Data Deduplication Health**): table _time, host, status, VolumeName, SavingsRate, CorruptionCount
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (savings rate over time), Table (job results), Single value (current savings %), Alert on corruption.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Deduplication*"
  EventCode IN (6153, 6155, 12800, 12802)
| eval status=case(EventCode=6153,"Optimization completed",EventCode=6155,"Optimization failed",EventCode=12800,"Scrubbing completed",EventCode=12802,"Corruption detected")
| table _time, host, status, VolumeName, SavingsRate, CorruptionCount
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.dest span=1h
| where count>0
```

## Visualization

Line chart (savings rate over time), Table (job results), Single value (current savings %), Alert on corruption.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
