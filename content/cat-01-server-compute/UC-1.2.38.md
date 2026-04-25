<!-- AUTO-GENERATED from UC-1.2.38.json — DO NOT EDIT -->

---
id: "1.2.38"
title: "AD Object Deletion Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.2.38 · AD Object Deletion Monitoring

## Description

Accidental or malicious deletion of AD objects (OUs, users, groups, computer accounts) can cause widespread service disruption. AD Recycle Bin has a limited window.

## Value

Surprise deletions are both operational risk (outage) and security risk (sabotage); one stream covers both with context.

## Implementation

Enable DS Object Access auditing on domain controllers. EventCode 5141 catches all AD object deletions including OUs. 4726/4730/4743 catch specific account/group/computer deletions. Alert on OU deletions immediately (mass impact). Track deletion volume per admin — spikes indicate accidental bulk operations or insider threats. Ensure AD Recycle Bin is enabled.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4726, 4730, 4743, 5141).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DS Object Access auditing on domain controllers. EventCode 5141 catches all AD object deletions including OUs. 4726/4730/4743 catch specific account/group/computer deletions. Alert on OU deletions immediately (mass impact). Track deletion volume per admin — spikes indicate accidental bulk operations or insider threats. Ensure AD Recycle Bin is enabled.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security"
  EventCode IN (4726, 4730, 4743, 5141)
| eval object_type=case(EventCode=4726,"User deleted",EventCode=4730,"Group deleted",EventCode=4743,"Computer deleted",EventCode=5141,"AD object deleted")
| table _time, host, object_type, SubjectUserName, TargetUserName, ObjectDN
| sort -_time
```

Understanding this SPL

**AD Object Deletion Monitoring** — Accidental or malicious deletion of AD objects (OUs, users, groups, computer accounts) can cause widespread service disruption. AD Recycle Bin has a limited window.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4726, 4730, 4743, 5141). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **object_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **AD Object Deletion Monitoring**): table _time, host, object_type, SubjectUserName, TargetUserName, ObjectDN
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (deleted objects), Timeline, Bar chart (deletions by admin), Single value (OU deletions — target: 0).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security"
  EventCode IN (4726, 4730, 4743, 5141)
| eval object_type=case(EventCode=4726,"User deleted",EventCode=4730,"Group deleted",EventCode=4743,"Computer deleted",EventCode=5141,"AD object deleted")
| table _time, host, object_type, SubjectUserName, TargetUserName, ObjectDN
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object span=1h
| where count>0
```

## Visualization

Table (deleted objects), Timeline, Bar chart (deletions by admin), Single value (OU deletions — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
