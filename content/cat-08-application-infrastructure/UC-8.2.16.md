---
id: "8.2.16"
title: "Node.js Event Loop Lag (High Resolution)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.16 · Node.js Event Loop Lag (High Resolution)

## Description

`eventLoopUtilization` and `delay` histogram from `perf_hooks` or Prometheus `nodejs_eventloop_lag_seconds` for sub-millisecond vs millisecond precision.

## Value

`eventLoopUtilization` and `delay` histogram from `perf_hooks` or Prometheus `nodejs_eventloop_lag_seconds` for sub-millisecond vs millisecond precision.

## Implementation

Export p50/p99 lag. Alert on p99 >50ms for 5m. Correlate with blocking `fs` or `dns` calls from traces.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenTelemetry, `prom-client`.
• Ensure the following data sources are available: `nodejs:metrics` `event_loop_lag_p99_ms`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Export p50/p99 lag. Alert on p99 >50ms for 5m. Correlate with blocking `fs` or `dns` calls from traces.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m perc99(event_loop_lag_ms) as p99_lag by host
| where p99_lag > 50
```

Understanding this SPL

**Node.js Event Loop Lag (High Resolution)** — `eventLoopUtilization` and `delay` histogram from `perf_hooks` or Prometheus `nodejs_eventloop_lag_seconds` for sub-millisecond vs millisecond precision.

Documented **Data sources**: `nodejs:metrics` `event_loop_lag_p99_ms`. **App/TA** (typical add-on context): OpenTelemetry, `prom-client`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: nodejs:metrics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="nodejs:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where p99_lag > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p99 event loop lag), Table (hosts breaching SLO), Single value (current p99).

## SPL

```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m perc99(event_loop_lag_ms) as p99_lag by host
| where p99_lag > 50
```

## Visualization

Line chart (p99 event loop lag), Table (hosts breaching SLO), Single value (current p99).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
