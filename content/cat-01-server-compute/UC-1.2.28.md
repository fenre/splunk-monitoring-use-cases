<!-- AUTO-GENERATED from UC-1.2.28.json — DO NOT EDIT -->

---
id: "1.2.28"
title: "Windows Firewall Rule Changes"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.28 · Windows Firewall Rule Changes

## Description

Unauthorized firewall rule changes can open attack vectors. Malware often disables the firewall or adds allow rules for C2 communication.

## Value

Firewall drift can silently open a server or break an app; tracking changes keeps security and app owners aligned.

## Implementation

Enable the Windows Firewall audit log. EventCode 2004=rule added, 2005=modified, 2006=deleted, 2033=firewall disabled. Alert immediately on firewall disabled events. Track rule changes against change management records. Focus on inbound allow rules added for non-standard ports.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable the Windows Firewall audit log. EventCode 2004=rule added, 2005=modified, 2006=deleted, 2033=firewall disabled. Alert immediately on firewall disabled events. Track rule changes against change management records. Focus on inbound allow rules added for non-standard ports.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall"
  EventCode IN (2004, 2005, 2006, 2033)
| eval action=case(EventCode=2004,"Rule Added",EventCode=2005,"Rule Modified",EventCode=2006,"Rule Deleted",EventCode=2033,"Firewall Disabled")
| table _time, host, action, RuleName, ApplicationPath, Direction, Protocol
| sort -_time
```

Understanding this SPL

**Windows Firewall Rule Changes** — Unauthorized firewall rule changes can open attack vectors. Malware often disables the firewall or adds allow rules for C2 communication.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Windows Firewall Rule Changes**): table _time, host, action, RuleName, ApplicationPath, Direction, Protocol
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Windows Firewall Rule Changes** — Unauthorized firewall rule changes can open attack vectors. Malware often disables the firewall or adds allow rules for C2 communication.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall` (EventCode 2004, 2005, 2006, 2033). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rule changes), Timeline, Single value (firewall disabled count — target: 0).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-Windows Firewall With Advanced Security/Firewall"
  EventCode IN (2004, 2005, 2006, 2033)
| eval action=case(EventCode=2004,"Rule Added",EventCode=2005,"Rule Modified",EventCode=2006,"Rule Deleted",EventCode=2033,"Firewall Disabled")
| table _time, host, action, RuleName, ApplicationPath, Direction, Protocol
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.object All_Changes.action All_Changes.dest span=1h
| where count>0
```

## Visualization

Table (rule changes), Timeline, Single value (firewall disabled count — target: 0).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
