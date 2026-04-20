---
id: "1.2.70"
title: "Context Switch Rate Anomalies (Windows)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.2.70 · Context Switch Rate Anomalies (Windows)

## Description

Abnormally high context switch rates indicate excessive threading, poor application design, or kernel-mode driver issues. Degrades overall system performance.

## Value

Abnormally high context switch rates indicate excessive threading, poor application design, or kernel-mode driver issues. Degrades overall system performance.

## Implementation

Add `Context Switches/sec` to Perfmon System inputs (interval=60). Normal range varies by workload — establish per-host baselines. >15,000/sec per CPU core is generally concerning. Alert when rate exceeds 2x the rolling baseline. Correlate with `Processor Queue Length` and `% Interrupt Time` to distinguish user-mode threading issues from driver/hardware interrupt storms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=Perfmon:System` (counter: Context Switches/sec).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Add `Context Switches/sec` to Perfmon System inputs (interval=60). Normal range varies by workload — establish per-host baselines. >15,000/sec per CPU core is generally concerning. Alert when rate exceeds 2x the rolling baseline. Correlate with `Processor Queue Length` and `% Interrupt Time` to distinguish user-mode threading issues from driver/hardware interrupt storms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:System" counter="Context Switches/sec"
| timechart span=5m avg(Value) as ctx_switches by host
| streamstats window=48 avg(ctx_switches) as baseline by host
| eval deviation = (ctx_switches - baseline) / baseline * 100
| where deviation > 100
```

Understanding this SPL

**Context Switch Rate Anomalies (Windows)** — Abnormally high context switch rates indicate excessive threading, poor application design, or kernel-mode driver issues. Degrades overall system performance.

Documented **Data sources**: `sourcetype=Perfmon:System` (counter: Context Switches/sec). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• `streamstats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **deviation** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where deviation > 100` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

Understanding this CIM / accelerated SPL

**Context Switch Rate Anomalies (Windows)** — Abnormally high context switch rates indicate excessive threading, poor application design, or kernel-mode driver issues. Degrades overall system performance.

Documented **Data sources**: `sourcetype=Perfmon:System` (counter: Context Switches/sec). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Performance` — enable acceleration for that model.
• Filters the current rows with `where avg_cpu > 90` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (context switch rate with baseline), Heatmap (hosts × rate), Single value (anomalous hosts).

## SPL

```spl
index=perfmon sourcetype="Perfmon:System" counter="Context Switches/sec"
| timechart span=5m avg(Value) as ctx_switches by host
| streamstats window=48 avg(ctx_switches) as baseline by host
| eval deviation = (ctx_switches - baseline) / baseline * 100
| where deviation > 100
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as avg_cpu
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where avg_cpu > 90
```

## Visualization

Line chart (context switch rate with baseline), Heatmap (hosts × rate), Single value (anomalous hosts).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
