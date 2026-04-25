<!-- AUTO-GENERATED from UC-8.7.2.json — DO NOT EDIT -->

---
id: "8.7.2"
title: "API Endpoint Latency Percentile Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-8.7.2 · API Endpoint Latency Percentile Trending

## Description

p50, p95, and p99 latency over 30 days highlights tail latency regressions that averages hide. Trends support SLO setting and regression detection after releases.

## Value

p50, p95, and p99 latency over 30 days highlights tail latency regressions that averages hide. Trends support SLO setting and regression detection after releases.

## Implementation

Normalize time units (seconds vs milliseconds) at ingest. Filter to API paths only; exclude static assets. Tag `service_name` for microservice drilldowns. Compare against canary or blue-green cohorts with a `deployment` field when available. Store weekly aggregates in `sourcetype=stash` for long retention.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: API gateway TAs (Kong, AWS API Gateway), reverse proxy logs, OpenTelemetry span export to Splunk.
• Ensure the following data sources are available: `index=web` or `index=app`, `sourcetype=access_combined` with response time, `index=middleware` gateway logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize time units (seconds vs milliseconds) at ingest. Filter to API paths only; exclude static assets. Tag `service_name` for microservice drilldowns. Compare against canary or blue-green cohorts with a `deployment` field when available. Store weekly aggregates in `sourcetype=stash` for long retention.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web OR index=app sourcetype=access_combined earliest=-30d
| eval ms=coalesce(response_time_ms, duration_ms, tonumber(substr(response_time,1,10)))
| where isnotnull(ms) AND match(uri_path,"/api/")
| timechart span=1d p50(ms) as p50 p95(ms) as p95 p99(ms) as p99
```

Understanding this SPL

**API Endpoint Latency Percentile Trending** — p50, p95, and p99 latency over 30 days highlights tail latency regressions that averages hide. Trends support SLO setting and regression detection after releases.

Documented **Data sources**: `index=web` or `index=app`, `sourcetype=access_combined` with response time, `index=middleware` gateway logs. **App/TA** (typical add-on context): API gateway TAs (Kong, AWS API Gateway), reverse proxy logs, OpenTelemetry span export to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web, app; **sourcetype**: access_combined. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=web, index=app, sourcetype=access_combined, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where isnotnull(ms) AND match(uri_path,"/api/")` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare with the application or platform source of truth (logs, UI, or metrics) for the same time range, and with known change or maintenance windows.


Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (p50/p95/p99 over time), heatmap (endpoint × day for p95), table (worst endpoints).

## SPL

```spl
index=web OR index=app sourcetype=access_combined earliest=-30d
| eval ms=coalesce(response_time_ms, duration_ms, tonumber(substr(response_time,1,10)))
| where isnotnull(ms) AND match(uri_path,"/api/")
| timechart span=1d p50(ms) as p50 p95(ms) as p95 p99(ms) as p99
```

## CIM SPL

```spl
| tstats `summariesonly` perc95(Web.duration) as p95_ms avg(Web.duration) as avg_ms
  from datamodel=Web.Web
  by Web.dest Web.uri_path span=5m
| where p95_ms > 2000
```

## Visualization

Line chart (p50/p95/p99 over time), heatmap (endpoint × day for p95), table (worst endpoints).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
