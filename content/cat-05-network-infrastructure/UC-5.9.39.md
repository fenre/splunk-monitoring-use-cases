---
id: "5.9.39"
title: "API Endpoint Completion Rate (ThousandEyes)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.39 · API Endpoint Completion Rate (ThousandEyes)

## Description

Monitors multi-step API test completion, ensuring that entire API workflows (authentication, data retrieval, processing) succeed end-to-end from external vantage points.

## Value

Monitors multi-step API test completion, ensuring that entire API workflows (authentication, data retrieval, processing) succeed end-to-end from external vantage points.

## Implementation

Create API tests in ThousandEyes with multi-step sequences testing your critical API workflows. The OTel metric `api.completion` reports overall completion percentage. Per-step metrics (`api.step.completion`, `api.step.duration`) are also available with the `thousandeyes.test.step` attribute. The Splunk App Application dashboard includes an "API Completion (%)" panel.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create API tests in ThousandEyes with multi-step sequences testing your critical API workflows. The OTel metric `api.completion` reports overall completion percentage. Per-step metrics (`api.step.completion`, `api.step.duration`) are also available with the `thousandeyes.test.step` attribute. The Splunk App Application dashboard includes an "API Completion (%)" panel.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```

Understanding this SPL

**API Endpoint Completion Rate (ThousandEyes)** — Monitors multi-step API test completion, ensuring that entire API workflows (authentication, data retrieval, processing) succeed end-to-end from external vantage points.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_completion < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (completion %), Line chart (completion over time), Table (test, completion).

## SPL

```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```

## Visualization

Single value (completion %), Line chart (completion over time), Table (test, completion).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
