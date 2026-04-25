<!-- AUTO-GENERATED from UC-5.9.38.json — DO NOT EDIT -->

---
id: "5.9.38"
title: "Page Load Duration Trending (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.38 · Page Load Duration Trending (ThousandEyes)

## Description

Tracks total page load time including all resources (HTML, CSS, JS, images). Trending reveals gradual degradation from growing page weight, slow third-party resources, or backend issues.

## Value

Tracks total page load time including all resources (HTML, CSS, JS, images). Trending reveals gradual degradation from growing page weight, slow third-party resources, or backend issues.

## Implementation

The OTel metric `web.page_load.duration` reports total page load time in seconds. The Splunk App Application dashboard includes a "Page Load Duration (s)" line chart with permalink drilldown to ThousandEyes waterfall views. Alert when load duration exceeds your performance budget.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `web.page_load.duration` reports total page load time in seconds. The Splunk App Application dashboard includes a "Page Load Duration (s)" line chart with permalink drilldown to ThousandEyes waterfall views. Alert when load duration exceeds your performance budget.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="page-load"
| timechart span=5m avg(web.page_load.duration) as avg_load_s by thousandeyes.test.name
```

Understanding this SPL

**Page Load Duration Trending (ThousandEyes)** — Tracks total page load time including all resources (HTML, CSS, JS, images). Trending reveals gradual degradation from growing page weight, slow third-party resources, or backend issues.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by thousandeyes.test.name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (load time over time), Single value (avg load time), Table with permalink drilldown.

## SPL

```spl
`stream_index` thousandeyes.test.type="page-load"
| timechart span=5m avg(web.page_load.duration) as avg_load_s by thousandeyes.test.name
```

## Visualization

Line chart (load time over time), Single value (avg load time), Table with permalink drilldown.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
