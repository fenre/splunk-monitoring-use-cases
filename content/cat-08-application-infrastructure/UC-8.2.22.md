<!-- AUTO-GENERATED from UC-8.2.22.json — DO NOT EDIT -->

---
id: "8.2.22"
title: ".NET Exception Rate Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.22 · .NET Exception Rate Trending

## Description

`# of Exceps Thrown / sec` and first-chance exception logs show error storms after deploys. Complements log-based UC-8.2.4 with runtime counters.

## Value

`# of Exceps Thrown / sec` and first-chance exception logs show error storms after deploys. Complements log-based UC-8.2.4 with runtime counters.

## Implementation

Baseline per process. Alert on 5× baseline. Join with deployment markers from UC-8.2.5.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` Perfmon, Serilog/NLog.
• Ensure the following data sources are available: `.NET CLR Exceptions` `# of Exceps Thrown / sec`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Baseline per process. Alert on 5× baseline. Join with deployment markers from UC-8.2.5.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=perfmon sourcetype="Perfmon:CLR_Exceptions"
| timechart span=5m sum(Exceps_Thrown_per_sec) as ex_rate by process_name
| eventstats avg(ex_rate) as baseline by process_name
| where ex_rate > baseline * 5 AND ex_rate > 1
```

Understanding this SPL

**.NET Exception Rate Trending** — `# of Exceps Thrown / sec` and first-chance exception logs show error storms after deploys. Complements log-based UC-8.2.4 with runtime counters.

Documented **Data sources**: `.NET CLR Exceptions` `# of Exceps Thrown / sec`. **App/TA** (typical add-on context): `Splunk_TA_windows` Perfmon, Serilog/NLog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: perfmon; **sourcetype**: Perfmon:CLR_Exceptions. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=perfmon, sourcetype="Perfmon:CLR_Exceptions". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by process_name** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by process_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where ex_rate > baseline * 5 AND ex_rate > 1` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (exception rate), Table (process, spike factor), Single value (total exceptions/sec).

## SPL

```spl
index=perfmon sourcetype="Perfmon:CLR_Exceptions"
| timechart span=5m sum(Exceps_Thrown_per_sec) as ex_rate by process_name
| eventstats avg(ex_rate) as baseline by process_name
| where ex_rate > baseline * 5 AND ex_rate > 1
```

## Visualization

Line chart (exception rate), Table (process, spike factor), Single value (total exceptions/sec).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
