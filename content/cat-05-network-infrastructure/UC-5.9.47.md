---
id: "5.9.47"
title: "ThousandEyes Alert Timeline Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.47 · ThousandEyes Alert Timeline Trending

## Description

Trending alert volume over time reveals patterns — recurring issues at specific times, increasing alert frequency indicating degradation, or correlation with change windows. Helps teams move from reactive to proactive operations.

## Value

Trending alert volume over time reveals patterns — recurring issues at specific times, increasing alert frequency indicating degradation, or correlation with change windows. Helps teams move from reactive to proactive operations.

## Implementation

The Splunk App Alerts dashboard includes a "Alerts Timeline" line chart and a "Severity Distribution Trend" chart. Use these pre-built panels or customize with the `stream_index` macro. Set adaptive alerts on alert volume increases — a sudden spike in ThousandEyes alerts often precedes user-reported incidents. Correlate alert timing with change management windows.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The Splunk App Alerts dashboard includes a "Alerts Timeline" line chart and a "Severity Distribution Trend" chart. Use these pre-built panels or customize with the `stream_index` macro. Set adaptive alerts on alert volume increases — a sudden spike in ThousandEyes alerts often precedes user-reported incidents. Correlate alert timing with change management windows.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` sourcetype="thousandeyes:alerts"
| timechart span=1h count by severity
```

Understanding this SPL

**ThousandEyes Alert Timeline Trending** — Trending alert volume over time reveals patterns — recurring issues at specific times, increasing alert frequency indicating degradation, or correlation with change windows. Helps teams move from reactive to proactive operations.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: thousandeyes:alerts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by severity** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (alerts over time by severity), Stacked bar chart (alerts per hour), Table (trending alert rules).

## SPL

```spl
`stream_index` sourcetype="thousandeyes:alerts"
| timechart span=1h count by severity
```

## Visualization

Line chart (alerts over time by severity), Stacked bar chart (alerts per hour), Table (trending alert rules).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
