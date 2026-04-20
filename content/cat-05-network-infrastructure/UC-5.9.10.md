---
id: "5.9.10"
title: "BGP Update Volume Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.9.10 · BGP Update Volume Tracking

## Description

High BGP update volumes can indicate route flapping, peer instability, or DDoS-related route manipulation. Trending helps establish baselines and detect anomalies.

## Value

High BGP update volumes can indicate route flapping, peer instability, or DDoS-related route manipulation. Trending helps establish baselines and detect anomalies.

## Implementation

The OTel metric `bgp.updates.count` tracks the number of BGP updates. The Splunk App Network dashboard includes a "BGP Updates Count" line chart. Set alerts when update volume exceeds 3 standard deviations from baseline.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `bgp.updates.count` tracks the number of BGP updates. The Splunk App Network dashboard includes a "BGP Updates Count" line chart. Set alerts when update volume exceeds 3 standard deviations from baseline.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.updates.count) as bgp_updates by thousandeyes.monitor.name
```

Understanding this SPL

**BGP Update Volume Tracking** — High BGP update volumes can indicate route flapping, peer instability, or DDoS-related route manipulation. Trending helps establish baselines and detect anomalies.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `timechart` plots the metric over time using **span=1h** buckets with a separate series **by thousandeyes.monitor.name** — ideal for trending and alerting on this use case.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (updates over time), Single value (current update rate), Table (monitor, prefix, update count).

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.updates.count) as bgp_updates by thousandeyes.monitor.name
```

## Visualization

Line chart (updates over time), Single value (current update rate), Table (monitor, prefix, update count).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
