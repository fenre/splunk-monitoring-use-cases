<!-- AUTO-GENERATED from UC-1.2.12.json — DO NOT EDIT -->

---
id: "1.2.12"
title: "RDP Session Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.12 · RDP Session Monitoring

## Description

Tracks who connected via Remote Desktop, from where, and when. Essential for compliance auditing and detecting lateral movement.

## Value

Proving who was on a server when something changed is a staple of support, audit, and incident response for Windows estates.

## Implementation

Enable Security log + TerminalServices operational log. Alert on RDP sessions to servers from unexpected sources. Create session audit report correlating logon/logoff events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType=10), `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Security log + TerminalServices operational log. Alert on RDP sessions to servers from unexpected sources. Create session audit report correlating logon/logoff events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" (EventCode=21 OR EventCode=23 OR EventCode=24 OR EventCode=25)
| table _time host User EventCode
```

Understanding this SPL

**RDP Session Monitoring** — Tracks who connected via Remote Desktop, from where, and when. Essential for compliance auditing and detecting lateral movement.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, LogonType=10), `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **RDP Session Monitoring**): table _time host User EventCode

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (user, source IP, host, time), Choropleth map for source IPs, Session timeline.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" (EventCode=21 OR EventCode=23 OR EventCode=24 OR EventCode=25)
| table _time host User EventCode
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count>0
```

## Visualization

Table (user, source IP, host, time), Choropleth map for source IPs, Session timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
