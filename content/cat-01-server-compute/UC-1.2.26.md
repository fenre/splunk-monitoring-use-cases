<!-- AUTO-GENERATED from UC-1.2.26.json — DO NOT EDIT -->

---
id: "1.2.26"
title: "Security Log Cleared"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.26 · Security Log Cleared

## Description

Clearing the Security event log is a classic attacker technique to cover tracks. Legitimate clears are rare and should always be investigated.

## Value

Log clearing is a classic attacker or insider cover-up move—an operator needs to act fast and preserve evidence the right way.

## Implementation

EventCode 1102 fires when the Security log is cleared; EventCode 104 when any event log is cleared. These should never occur in production outside controlled maintenance windows. Set a real-time alert with critical priority. Enrich with user identity to track who performed the action.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 1102), `sourcetype=WinEventLog:System` (EventCode 104).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 1102 fires when the Security log is cleared; EventCode 104 when any event log is cleared. These should never occur in production outside controlled maintenance windows. Set a real-time alert with critical priority. Enrich with user identity to track who performed the action.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog (sourcetype="WinEventLog:Security" EventCode=1102) OR (sourcetype="WinEventLog:System" EventCode=104)
| table _time, host, sourcetype, EventCode, SubjectUserName, SubjectDomainName
| sort -_time
```

Understanding this SPL

**Security Log Cleared** — Clearing the Security event log is a classic attacker technique to cover tracks. Legitimate clears are rare and should always be investigated.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 1102), `sourcetype=WinEventLog:System` (EventCode 104). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security, WinEventLog:System. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Security Log Cleared**): table _time, host, sourcetype, EventCode, SubjectUserName, SubjectDomainName
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.action All_Changes.object span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (clear events), Table (who cleared what), Single value (count — target: 0).

## SPL

```spl
index=wineventlog (sourcetype="WinEventLog:Security" EventCode=1102) OR (sourcetype="WinEventLog:System" EventCode=104)
| table _time, host, sourcetype, EventCode, SubjectUserName, SubjectDomainName
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.action All_Changes.object span=1h
| where count>0
```

## Visualization

Timeline (clear events), Table (who cleared what), Single value (count — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
