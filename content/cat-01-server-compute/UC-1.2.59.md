<!-- AUTO-GENERATED from UC-1.2.59.json — DO NOT EDIT -->

---
id: "1.2.59"
title: "DCOM / COM+ Application Errors"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.59 · DCOM / COM+ Application Errors

## Description

DCOM errors affect distributed applications, WMI remote management, and MMC snap-ins. Persistent errors indicate permission issues or component registration corruption.

## Value

When DCOM is really broken, random enterprise apps that depend on in-proc calls fail in odd ways—trend, don’t one-off every 10016.

## Implementation

EventCode 10016=permission error (most common — often benign for built-in COM objects), 10028=DCOM connection timed out, 10010=server did not register within timeout. Filter known benign 10016 errors (Windows built-in CLSIDs). Alert on 10028/10010 as these indicate application-impacting failures. Persistent 10010 errors for specific CLSIDs indicate broken COM registrations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (EventCode 10016, 10028, 10010).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 10016=permission error (most common — often benign for built-in COM objects), 10028=DCOM connection timed out, 10010=server did not register within timeout. Filter known benign 10016 errors (Windows built-in CLSIDs). Alert on 10028/10010 as these indicate application-impacting failures. Persistent 10010 errors for specific CLSIDs indicate broken COM registrations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="DCOM" EventCode IN (10016, 10028, 10010)
| stats count by host, EventCode, param1, param2
| where count > 10
| sort -count
```

Understanding this SPL

**DCOM / COM+ Application Errors** — DCOM errors affect distributed applications, WMI remote management, and MMC snap-ins. Persistent errors indicate permission issues or component registration corruption.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 10016, 10028, 10010). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, EventCode, param1, param2** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DCOM errors by CLSID), Bar chart (error types), Timechart (error frequency).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="DCOM" EventCode IN (10016, 10028, 10010)
| stats count by host, EventCode, param1, param2
| where count > 10
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object span=1h
| where count>0
```

## Visualization

Table (DCOM errors by CLSID), Bar chart (error types), Timechart (error frequency).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
