<!-- AUTO-GENERATED from UC-8.2.9.json — DO NOT EDIT -->

---
id: "8.2.9"
title: "Node.js Event Loop Lag"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.2.9 · Node.js Event Loop Lag

## Description

Event loop lag indicates blocking operations that prevent Node.js from handling requests. Detection enables code-level investigation.

## Value

Event loop lag indicates blocking operations that prevent Node.js from handling requests. Detection enables code-level investigation.

## Implementation

Instrument Node.js apps with `prom-client` or OpenTelemetry SDK. Export event loop lag, heap stats, and active handles/requests. Forward to Splunk via HEC or Prometheus remote write. Alert when lag exceeds 100ms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom metrics input, OpenTelemetry.
• Ensure the following data sources are available: Node.js process metrics (event loop lag, heap usage), Prometheus client metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Instrument Node.js apps with `prom-client` or OpenTelemetry SDK. Export event loop lag, heap stats, and active handles/requests. Forward to Splunk via HEC or Prometheus remote write. Alert when lag exceeds 100ms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m avg(event_loop_lag_ms) as el_lag, avg(heap_used_mb) as heap by host
| where el_lag > 100
```

Understanding this SPL

**Node.js Event Loop Lag** — Event loop lag indicates blocking operations that prevent Node.js from handling requests. Detection enables code-level investigation.

Documented **Data sources**: Node.js process metrics (event loop lag, heap usage), Prometheus client metrics. **App/TA** (typical add-on context): Custom metrics input, OpenTelemetry. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: application; **sourcetype**: nodejs:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=application, sourcetype="nodejs:metrics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where el_lag > 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare with JBoss, WebLogic, or Tomcat admin consoles, or `catalina` / server logs on the host, for the same window. Confirm hostnames and fields match the vendor UI.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (event loop lag), Dual-axis (lag + heap usage), Single value (current lag ms).

## SPL

```spl
index=application sourcetype="nodejs:metrics"
| timechart span=1m avg(event_loop_lag_ms) as el_lag, avg(heap_used_mb) as heap by host
| where el_lag > 100
```

## Visualization

Line chart (event loop lag), Dual-axis (lag + heap usage), Single value (current lag ms).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
