<!-- AUTO-GENERATED from UC-1.2.103.json — DO NOT EDIT -->

---
id: "1.2.103"
title: "Terminal Services / RDP Session Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.103 · Terminal Services / RDP Session Tracking

## Description

RDP is a primary lateral movement vector. Complete session tracking from logon to logoff enables detection of compromised credentials and unauthorized access.

## Value

RDP session history supports both security (shared admin accounts, odd hours) and operations (capacity, license, and FSLogix health) on session hosts.

## Implementation

Collect TerminalServices-LocalSessionManager/Operational log for session lifecycle events. Track logon (21), logoff (23), disconnect (24), reconnect (25). Correlate with Security log 4624 Type 10 for source IP. Alert on RDP to servers from non-admin workstations, sessions during off-hours, and multiple concurrent sessions from different IPs for same user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`, `sourcetype=WinEventLog:Security`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect TerminalServices-LocalSessionManager/Operational log for session lifecycle events. Track logon (21), logoff (23), disconnect (24), reconnect (25). Correlate with Security log 4624 Type 10 for source IP. Alert on RDP to servers from non-admin workstations, sessions during off-hours, and multiple concurrent sessions from different IPs for same user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" EventCode IN (21, 23, 24, 25)
| eval Action=case(EventCode=21,"Logon", EventCode=23,"Logoff", EventCode=24,"Disconnect", EventCode=25,"Reconnect", 1=1,"Other")
| eval src=if(isnotnull(Address), Address, "local")
| stats earliest(_time) as SessionStart latest(_time) as SessionEnd values(Action) as Actions by host, User, SessionID, src
| eval Duration=round((SessionEnd-SessionStart)/60,1)
```

Understanding this SPL

**Terminal Services / RDP Session Tracking** — RDP is a primary lateral movement vector. Complete session tracking from logon to logoff enables detection of compromised credentials and unauthorized access.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational`, `sourcetype=WinEventLog:Security`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Action** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **src** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, User, SessionID, src** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **Duration** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (sessions), Table (session details), Alert on anomalous patterns.

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-LocalSessionManager/Operational" EventCode IN (21, 23, 24, 25)
| eval Action=case(EventCode=21,"Logon", EventCode=23,"Logoff", EventCode=24,"Disconnect", EventCode=25,"Reconnect", 1=1,"Other")
| eval src=if(isnotnull(Address), Address, "local")
| stats earliest(_time) as SessionStart latest(_time) as SessionEnd values(Action) as Actions by host, User, SessionID, src
| eval Duration=round((SessionEnd-SessionStart)/60,1)
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 0
```

## Visualization

Timeline (sessions), Table (session details), Alert on anomalous patterns.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
