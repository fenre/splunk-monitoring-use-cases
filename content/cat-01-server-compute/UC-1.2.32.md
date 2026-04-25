<!-- AUTO-GENERATED from UC-1.2.32.json — DO NOT EDIT -->

---
id: "1.2.32"
title: "WMI Event Subscription Persistence"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.32 · WMI Event Subscription Persistence

## Description

WMI event subscriptions are a stealthy persistence mechanism that survives reboots. Used by APT groups and fileless malware.

## Value

WMI persistence is silent and durable—this view supports proactive hunts, not just cleanup after a scanner finds something.

## Implementation

Deploy Sysmon v10+ which logs WMI event filter (19), consumer (20), and binding (21) creation. Any new WMI subscription outside management tools (SCCM, monitoring agents) is suspicious. Alert on all new subscriptions. Legitimate ones are rare and well-known (e.g., SCCM client). Correlate consumer CommandLineTemplate with known malware signatures.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, Sysmon required.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Sysmon v10+ which logs WMI event filter (19), consumer (20), and binding (21) creation. Any new WMI subscription outside management tools (SCCM, monitoring agents) is suspicious. Alert on all new subscriptions. Legitimate ones are rare and well-known (e.g., SCCM client). Correlate consumer CommandLineTemplate with known malware signatures.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (19, 20, 21)
| eval wmi_type=case(EventCode=19,"Filter Created",EventCode=20,"Consumer Created",EventCode=21,"Binding Created")
| table _time, host, wmi_type, User, Name, Destination, Query
| sort -_time
```

Understanding this SPL

**WMI Event Subscription Persistence** — WMI event subscriptions are a stealthy persistence mechanism that survives reboots. Used by APT groups and fileless malware.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-Sysmon/Operational` (EventCode 19, 20, 21). **App/TA** (typical add-on context): `Splunk_TA_windows`, Sysmon required. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-Sysmon/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **wmi_type** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **WMI Event Subscription Persistence**): table _time, host, wmi_type, User, Name, Destination, Query
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
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (WMI subscriptions created), Timeline, Single value (new subscriptions — target: 0 outside SCCM).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-Sysmon/Operational"
  EventCode IN (19, 20, 21)
| eval wmi_type=case(EventCode=19,"Filter Created",EventCode=20,"Consumer Created",EventCode=21,"Binding Created")
| table _time, host, wmi_type, User, Name, Destination, Query
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

Table (WMI subscriptions created), Timeline, Single value (new subscriptions — target: 0 outside SCCM).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
