---
id: "5.9.42"
title: "Transaction Duration Analysis (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.42 · Transaction Duration Analysis (ThousandEyes)

## Description

Measures end-to-end time for complex user workflows. Slow transactions directly impact user productivity and satisfaction. Trending reveals gradual degradation across the multi-step flow.

## Value

Measures end-to-end time for complex user workflows. Slow transactions directly impact user productivity and satisfaction. Trending reveals gradual degradation across the multi-step flow.

## Implementation

The OTel metric `web.transaction.duration` reports total transaction execution time in seconds (only reported when the transaction completes without errors). The Splunk App Application dashboard includes a "Transaction Duration (s)" line chart with permalink drilldown to ThousandEyes. ThousandEyes also supports OpenTelemetry traces for transaction tests, providing detailed span-level timing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `web.transaction.duration` reports total transaction execution time in seconds (only reported when the transaction completes without errors). The Splunk App Application dashboard includes a "Transaction Duration (s)" line chart with permalink drilldown to ThousandEyes. ThousandEyes also supports OpenTelemetry traces for transaction tests, providing detailed span-level timing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| timechart span=5m avg(web.transaction.duration) as avg_transaction_s by thousandeyes.test.name
```

Understanding this SPL

**Transaction Duration Analysis (ThousandEyes)** — Measures end-to-end time for complex user workflows. Slow transactions directly impact user productivity and satisfaction. Trending reveals gradual degradation across the multi-step flow.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by thousandeyes.test.name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (transaction duration over time), Table (test, agent, duration), Drilldown to ThousandEyes trace view.

## SPL

```spl
`stream_index` thousandeyes.test.type="web-transactions"
| timechart span=5m avg(web.transaction.duration) as avg_transaction_s by thousandeyes.test.name
```

## Visualization

Line chart (transaction duration over time), Table (test, agent, duration), Drilldown to ThousandEyes trace view.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
