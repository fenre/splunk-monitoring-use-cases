<!-- AUTO-GENERATED from UC-1.2.47.json — DO NOT EDIT -->

---
id: "1.2.47"
title: "Application Crash (WER) Trending"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.47 · Application Crash (WER) Trending

## Description

Windows Error Reporting captures crash details for all applications. Trending reveals systemic instability, bad patches, or problematic application versions.

## Value

Repeat crashes are a leading indicator of bad patches, bad code, and dependency drift—trend, not a single 1000 event.

## Implementation

EventCode 1000=application crash with fault details (module, exception code, offset), 1002=application hang detected. Aggregate by faulting application and module across the fleet. Spikes after patch deployment indicate regression. Alert on critical applications (e.g., w3wp.exe, sqlservr.exe, lsass.exe). Use EventCode 1001 (WER bucket data) for deduplication.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Application` (EventCode 1000, 1001, 1002).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 1000=application crash with fault details (module, exception code, offset), 1002=application hang detected. Aggregate by faulting application and module across the fleet. Spikes after patch deployment indicate regression. Alert on critical applications (e.g., w3wp.exe, sqlservr.exe, lsass.exe). Use EventCode 1001 (WER bucket data) for deduplication.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Application" EventCode IN (1000, 1002)
| eval crash_app=coalesce(Application, param1)
| stats count by host, crash_app, EventCode
| where count > 3
| sort -count
```

Understanding this SPL

**Application Crash (WER) Trending** — Windows Error Reporting captures crash details for all applications. Trending reveals systemic instability, bad patches, or problematic application versions.

Documented **Data sources**: `sourcetype=WinEventLog:Application` (EventCode 1000, 1001, 1002). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Application. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Application". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **crash_app** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, crash_app, EventCode** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Application_State
  by host span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Application Crash (WER) Trending** — Windows Error Reporting captures crash details for all applications. Trending reveals systemic instability, bad patches, or problematic application versions.

Documented **Data sources**: `sourcetype=WinEventLog:Application` (EventCode 1000, 1001, 1002). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top crashing apps), Timechart (crash rate over time), Table (crash details by module).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Application" EventCode IN (1000, 1002)
| eval crash_app=coalesce(Application, param1)
| stats count by host, crash_app, EventCode
| where count > 3
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Application_State
  by host span=1h
| where count>0
```

## Visualization

Bar chart (top crashing apps), Timechart (crash rate over time), Table (crash details by module).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
