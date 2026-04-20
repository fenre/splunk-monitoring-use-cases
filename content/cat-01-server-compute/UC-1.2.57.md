---
id: "1.2.57"
title: "Thread Count Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.57 · Thread Count Exhaustion

## Description

Thread leaks or excessive thread creation cause pool exhaustion and application hangs. Windows has a system-wide limit of ~65K threads that affects all processes.

## Value

Thread leaks or excessive thread creation cause pool exhaustion and application hangs. Windows has a system-wide limit of ~65K threads that affects all processes.

## Implementation

Configure Perfmon Process inputs with `Thread Count` counter (interval=300). Also monitor system-wide threads via Perfmon System → Threads. Alert when any single process exceeds 500 threads or system total exceeds 50K. Common offenders: IIS application pools (w3wp.exe), Java applications, .NET services with async leaks. Correlate with application response times.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:Process` (counter: Thread Count), `sourcetype=Perfmon:System` (counter: Threads).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Perfmon Process inputs with `Thread Count` counter (interval=300). Also monitor system-wide threads via Perfmon System → Threads. Alert when any single process exceeds 500 threads or system total exceeds 50K. Common offenders: IIS application pools (w3wp.exe), Java applications, .NET services with async leaks. Correlate with application response times.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:Process" counter="Thread Count" instance!="_Total" instance!="Idle"
| stats max(Value) as threads by host, instance
| where threads > 500
| sort -threads
```

Understanding this SPL

**Thread Count Exhaustion** — Thread leaks or excessive thread creation cause pool exhaustion and application hangs. Windows has a system-wide limit of ~65K threads that affects all processes.

Documented **Data sources**: `sourcetype=Perfmon:Process` (counter: Thread Count), `sourcetype=Perfmon:System` (counter: Threads). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:Process. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:Process". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, instance** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where threads > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**Thread Count Exhaustion** — Thread leaks or excessive thread creation cause pool exhaustion and application hangs. Windows has a system-wide limit of ~65K threads that affects all processes.

Documented **Data sources**: `sourcetype=Perfmon:Process` (counter: Thread Count), `sourcetype=Perfmon:System` (counter: Threads). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (top thread consumers), Line chart (thread growth trend), Single value (system total).

## SPL

```spl
index=perfmon sourcetype="Perfmon:Process" counter="Thread Count" instance!="_Total" instance!="Idle"
| stats max(Value) as threads by host, instance
| where threads > 500
| sort -threads
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Bar chart (top thread consumers), Line chart (thread growth trend), Single value (system total).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
