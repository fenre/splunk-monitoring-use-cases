<!-- AUTO-GENERATED from UC-5.9.35.json — DO NOT EDIT -->

---
id: "5.9.35"
title: "HTTP Server Response Time Tracking (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.35 · HTTP Server Response Time Tracking (ThousandEyes)

## Description

Tracks Time to First Byte (TTFB) from ThousandEyes agents to web servers. Rising response times indicate backend degradation, infrastructure bottlenecks, or increased load — often visible from external vantage points before internal monitoring catches it.

## Value

Tracks Time to First Byte (TTFB) from ThousandEyes agents to web servers. Rising response times indicate backend degradation, infrastructure bottlenecks, or increased load — often visible from external vantage points before internal monitoring catches it.

## Implementation

The OTel metric `http.client.request.duration` reports TTFB in seconds. The Splunk App Application dashboard includes an "HTTP Server Request Duration (s)" line chart. Alert when TTFB exceeds your SLA threshold (e.g., 2 seconds). Correlate with `http.response.status_code` to distinguish slow responses from errors.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `http.client.request.duration` reports TTFB in seconds. The Splunk App Application dashboard includes an "HTTP Server Request Duration (s)" line chart. Alert when TTFB exceeds your SLA threshold (e.g., 2 seconds). Correlate with `http.response.status_code` to distinguish slow responses from errors.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server"
| timechart span=5m avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
```

Understanding this SPL

**HTTP Server Response Time Tracking (ThousandEyes)** — Tracks Time to First Byte (TTFB) from ThousandEyes agents to web servers. Rising response times indicate backend degradation, infrastructure bottlenecks, or increased load — often visible from external vantage points before internal monitoring catches it.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by thousandeyes.test.name** — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **avg_ttfb_ms** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (TTFB over time by test), Single value (avg TTFB), Table with drilldown to ThousandEyes.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| timechart span=5m avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
```

## Visualization

Line chart (TTFB over time by test), Single value (avg TTFB), Table with drilldown to ThousandEyes.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
