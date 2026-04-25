<!-- AUTO-GENERATED from UC-5.9.9.json — DO NOT EDIT -->

---
id: "5.9.9"
title: "BGP Path Change Trending"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.9 · BGP Path Change Trending

## Description

BGP path changes indicate routing instability. Frequent path changes can cause traffic to take sub-optimal routes, increasing latency or traversing unexpected transit providers.

## Value

BGP path changes indicate routing instability. Frequent path changes can cause traffic to take sub-optimal routes, increasing latency or traversing unexpected transit providers.

## Implementation

The OTel metric `bgp.path_changes.count` tracks the number of route changes per collection interval. The Splunk App Network dashboard includes a "BGP Path Changes Count" line chart. Correlate spikes with ISP maintenance windows or upstream provider issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `bgp.path_changes.count` tracks the number of route changes per collection interval. The Splunk App Network dashboard includes a "BGP Path Changes Count" line chart. Correlate spikes with ISP maintenance windows or upstream provider issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.path_changes.count) as path_changes by thousandeyes.monitor.name
```

Understanding this SPL

**BGP Path Change Trending** — BGP path changes indicate routing instability. Frequent path changes can cause traffic to take sub-optimal routes, increasing latency or traversing unexpected transit providers.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by thousandeyes.monitor.name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (path changes over time per monitor), Bar chart (total changes per monitor), Table with drilldown.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.path_changes.count) as path_changes by thousandeyes.monitor.name
```

## Visualization

Line chart (path changes over time per monitor), Bar chart (total changes per monitor), Table with drilldown.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
