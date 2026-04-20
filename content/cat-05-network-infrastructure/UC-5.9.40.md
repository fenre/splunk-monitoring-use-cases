---
id: "5.9.40"
title: "API Response Time Monitoring (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.40 · API Response Time Monitoring (ThousandEyes)

## Description

Tracks total API test execution duration including all steps, revealing when API performance degrades from the consumer's perspective.

## Value

Tracks total API test execution duration including all steps, revealing when API performance degrades from the consumer's perspective.

## Implementation

The OTel metric `api.duration` reports total API test execution time in seconds. For per-step analysis, use `api.step.duration` filtered by `thousandeyes.test.step`. The Splunk App Application dashboard includes an "API Request Duration (s)" line chart with permalink drilldown.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `api.duration` reports total API test execution time in seconds. For per-step analysis, use `api.step.duration` filtered by `thousandeyes.test.step`. The Splunk App Application dashboard includes an "API Request Duration (s)" line chart with permalink drilldown.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="api"
| timechart span=5m avg(api.duration) as avg_api_duration_s by thousandeyes.test.name
```

Understanding this SPL

**API Response Time Monitoring (ThousandEyes)** — Tracks total API test execution duration including all steps, revealing when API performance degrades from the consumer's perspective.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by thousandeyes.test.name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (API duration over time), Table (test, duration), Column chart (duration by step).

## SPL

```spl
`stream_index` thousandeyes.test.type="api"
| timechart span=5m avg(api.duration) as avg_api_duration_s by thousandeyes.test.name
```

## Visualization

Line chart (API duration over time), Table (test, duration), Column chart (duration by step).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
