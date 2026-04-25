<!-- AUTO-GENERATED from UC-5.9.49.json — DO NOT EDIT -->

---
id: "5.9.49"
title: "ThousandEyes Data Collection Health Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.49 · ThousandEyes Data Collection Health Monitoring

## Description

Monitors the health of the ThousandEyes-to-Splunk data pipeline itself. Detects gaps in data collection, API errors, or HEC delivery failures that would cause blind spots in network and application monitoring.

## Value

Monitors the health of the ThousandEyes-to-Splunk data pipeline itself. Detects gaps in data collection, API errors, or HEC delivery failures that would cause blind spots in network and application monitoring.

## Implementation

Monitor the data flow from ThousandEyes to Splunk by tracking event volume per collection interval. A drop to zero events indicates a pipeline failure — possible causes include expired ThousandEyes API tokens, HEC token issues, or ThousandEyes streaming configuration changes. Combine with `index=_internal sourcetype=splunkd component=HttpInputDataHandler` to monitor HEC health. The Splunk App Health dashboard provides data freshness panels.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, Splunk internal logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor the data flow from ThousandEyes to Splunk by tracking event volume per collection interval. A drop to zero events indicates a pipeline failure — possible causes include expired ThousandEyes API tokens, HEC token issues, or ThousandEyes streaming configuration changes. Combine with `index=_internal sourcetype=splunkd component=HttpInputDataHandler` to monitor HEC health. The Splunk App Health dashboard provides data freshness panels.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index`
| timechart span=5m count as event_count
| where event_count < 1
```

Understanding this SPL

**ThousandEyes Data Collection Health Monitoring** — Monitors the health of the ThousandEyes-to-Splunk data pipeline itself. Detects gaps in data collection, API errors, or HEC delivery failures that would cause blind spots in network and application monitoring.

Documented **Data sources**: `index=thousandeyes`, Splunk internal logs. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• Filters the current rows with `where event_count < 1` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (event volume over time), Single value (events in last 5 min), Alert on zero events for >15 min.

## SPL

```spl
`stream_index`
| timechart span=5m count as event_count
| where event_count < 1
```

## Visualization

Line chart (event volume over time), Single value (events in last 5 min), Alert on zero events for >15 min.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
