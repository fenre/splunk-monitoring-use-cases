<!-- AUTO-GENERATED from UC-1.2.27.json — DO NOT EDIT -->

---
id: "1.2.27"
title: "New Service Installation"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.27 · New Service Installation

## Description

Attackers install malicious services for persistence. Unexpected service installations outside change windows indicate compromise or unauthorized software.

## Value

Persistence often starts with a new service—catching that beats chasing symptoms after the back door is in.

## Implementation

EventCode 7045 logs every new service installation. Filter out known/expected services via a lookup of approved service names. Alert on services with binaries outside standard paths (C:\Windows, C:\Program Files). Pay special attention to services running as SYSTEM with binaries in temp directories.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (EventCode 7045).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 7045 logs every new service installation. Filter out known/expected services via a lookup of approved service names. Alert on services with binaries outside standard paths (C:\Windows, C:\Program Files). Pay special attention to services running as SYSTEM with binaries in temp directories.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=7045
| table _time, host, ServiceName, ImagePath, ServiceType, AccountName
| regex ImagePath!="(?i)(C:\\\\Windows\\\\|C:\\\\Program Files)"
| sort -_time
```

Understanding this SPL

**New Service Installation** — Attackers install malicious services for persistence. Unexpected service installations outside change windows indicate compromise or unauthorized software.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 7045). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **New Service Installation**): table _time, host, ServiceName, ImagePath, ServiceType, AccountName
• Filters rows matching a pattern with `regex`.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**New Service Installation** — Attackers install malicious services for persistence. Unexpected service installations outside change windows indicate compromise or unauthorized software.

Documented **Data sources**: `sourcetype=WinEventLog:System` (EventCode 7045). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (new services with paths), Timeline, Alert on non-standard paths.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" EventCode=7045
| table _time, host, ServiceName, ImagePath, ServiceType, AccountName
| regex ImagePath!="(?i)(C:\\\\Windows\\\\|C:\\\\Program Files)"
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.user All_Changes.object All_Changes.dest span=1h
| where count>0
```

## Visualization

Table (new services with paths), Timeline, Alert on non-standard paths.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
