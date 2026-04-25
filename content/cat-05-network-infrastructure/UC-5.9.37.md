<!-- AUTO-GENERATED from UC-5.9.37.json — DO NOT EDIT -->

---
id: "5.9.37"
title: "Page Load Completion Rate (ThousandEyes)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.37 · Page Load Completion Rate (ThousandEyes)

## Description

Measures whether web pages fully load from the user's perspective. Incomplete page loads indicate broken resources, blocked CDN content, or JavaScript errors that prevent users from completing tasks.

## Value

Measures whether web pages fully load from the user's perspective. Incomplete page loads indicate broken resources, blocked CDN content, or JavaScript errors that prevent users from completing tasks.

## Implementation

Create Page Load tests in ThousandEyes targeting critical web applications. The OTel metric `web.page_load.completion` reports 100% when the page loads successfully and 0% on error. Page Load tests automatically include underlying Agent-to-Server network tests, providing correlated network and application data.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create Page Load tests in ThousandEyes targeting critical web applications. The OTel metric `web.page_load.completion` reports 100% when the page loads successfully and 0% on error. Page Load tests automatically include underlying Agent-to-Server network tests, providing correlated network and application data.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion by thousandeyes.test.name, server.address
| where avg_completion < 100
| sort avg_completion
```

Understanding this SPL

**Page Load Completion Rate (ThousandEyes)** — Measures whether web pages fully load from the user's perspective. Incomplete page loads indicate broken resources, blocked CDN content, or JavaScript errors that prevent users from completing tasks.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, server.address** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_completion < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (completion %), Line chart (completion over time), Table (test, server, completion).

## SPL

```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion by thousandeyes.test.name, server.address
| where avg_completion < 100
| sort avg_completion
```

## Visualization

Single value (completion %), Line chart (completion over time), Table (test, server, completion).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
