<!-- AUTO-GENERATED from UC-1.2.19.json — DO NOT EDIT -->

---
id: "1.2.19"
title: "Group Policy Processing Failures"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.19 · Group Policy Processing Failures

## Description

GPO failures mean security policies, drive mappings, software deployments, and configurations aren't being applied. Systems may be running with stale or missing policies.

## Value

Unapplied GPOs mean missing controls and broken maps—this helps close the loop before user drift and audit findings do.

## Implementation

Enable Group Policy operational log forwarding. Alert on persistent GPO failures per host. Correlate with network connectivity (DC reachability) and DNS resolution issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-GroupPolicy/Operational`, EventCodes 1085, 1096.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Group Policy operational log forwarding. Alert on persistent GPO failures per host. Correlate with network connectivity (DC reachability) and DNS resolution issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-GroupPolicy/Operational" (EventCode=1085 OR EventCode=1096 OR EventCode=7016 OR EventCode=7320)
| stats count by host, EventCode, ErrorDescription
| sort -count
```

Understanding this SPL

**Group Policy Processing Failures** — GPO failures mean security policies, drive mappings, software deployments, and configurations aren't being applied. Systems may be running with stale or missing policies.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-GroupPolicy/Operational`, EventCodes 1085, 1096. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-GroupPolicy/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-GroupPolicy/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, EventCode, ErrorDescription** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object All_Changes.action span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Group Policy Processing Failures** — GPO failures mean security policies, drive mappings, software deployments, and configurations aren't being applied. Systems may be running with stale or missing policies.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-GroupPolicy/Operational`, EventCodes 1085, 1096. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Change.All_Changes` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, error, count), Bar chart by error type.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-GroupPolicy/Operational" (EventCode=1085 OR EventCode=1096 OR EventCode=7016 OR EventCode=7320)
| stats count by host, EventCode, ErrorDescription
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest All_Changes.object All_Changes.action span=1h
| where count>0
```

## Visualization

Table (host, error, count), Bar chart by error type.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Change](https://docs.splunk.com/Documentation/CIM/latest/User/Change)
