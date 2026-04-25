<!-- AUTO-GENERATED from UC-1.2.22.json — DO NOT EDIT -->

---
id: "1.2.22"
title: "Process Handle Leak Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.22 · Process Handle Leak Detection

## Description

Handle leaks cause resource exhaustion and eventual application crashes or system instability. Detecting the leak early prevents unplanned outages.

## Value

Handle leaks are slow failures—spotting a rising trend saves an outage you only notice after the app dies.

## Implementation

Configure Perfmon Process inputs with `Handle Count` counter, all instances, interval=300. Alert when a process shows sustained handle growth >50% over 24-hour baseline. Common leakers: w3wp.exe, svchost.exe, custom .NET apps. Correlate with application restarts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:Process` (counter: Handle Count).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon Process inputs with `Handle Count` counter, all instances, interval=300. Alert when a process shows sustained handle growth >50% over 24-hour baseline. Common leakers: w3wp.exe, svchost.exe, custom .NET apps. Correlate with application restarts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:Process" counter="Handle Count" instance!="_Total" instance!="Idle"
| timechart span=1h max(Value) as handles by host, instance
| streamstats window=24 current=f avg(handles) as avg_handles by host, instance
| eval pct_increase = round((handles - avg_handles) / avg_handles * 100, 1)
| where pct_increase > 50 AND handles > 5000
```

Understanding this SPL

**Process Handle Leak Detection** — Handle leaks cause resource exhaustion and eventual application crashes or system instability. Detecting the leak early prevents unplanned outages.

Documented **Data sources**: `sourcetype=Perfmon:Process` (counter: Handle Count). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:Process. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:Process". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by host, instance** — ideal for trending and alerting on this use case.
• `streamstats` rolls up events into metrics; results are split **by host, instance** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **pct_increase** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pct_increase > 50 AND handles > 5000` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.process_name Processes.user Processes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Process Handle Leak Detection** — Handle leaks cause resource exhaustion and eventual application crashes or system instability. Detecting the leak early prevents unplanned outages.

Documented **Data sources**: `sourcetype=Perfmon:Process` (counter: Handle Count). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` on the CIM data model in `cimModels` (see the accelerated SPL block). Enable that model in Data Model Acceleration.
• The `where` and `by` clauses mirror the intent of the primary SPL; if tstats is empty, confirm field aliases in Splunk CIM and the Windows TA.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (handle trend per process), Table (top handle consumers), Alert on sustained growth.

## SPL

```spl
index=perfmon sourcetype="Perfmon:Process" counter="Handle Count" instance!="_Total" instance!="Idle"
| timechart span=1h max(Value) as handles by host, instance
| streamstats window=24 current=f avg(handles) as avg_handles by host, instance
| eval pct_increase = round((handles - avg_handles) / avg_handles * 100, 1)
| where pct_increase > 50 AND handles > 5000
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint where nodename=Endpoint.Processes
  by Processes.process_name Processes.user Processes.dest span=1h
| where count>0
```

## Visualization

Line chart (handle trend per process), Table (top handle consumers), Alert on sustained growth.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
