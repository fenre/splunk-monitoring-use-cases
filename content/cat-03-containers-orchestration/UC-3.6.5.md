---
id: "3.6.5"
title: "Kubernetes Event Error Rate Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.5 · Kubernetes Event Error Rate Trending

## Description

Warning and error Kubernetes events aggregate noise from image pulls, scheduling failures, and control-plane issues. A rising daily rate of Warning/Error events signals systemic problems even when individual alerts are not firing.

## Value

Warning and error Kubernetes events aggregate noise from image pulls, scheduling failures, and control-plane issues. A rising daily rate of Warning/Error events signals systemic problems even when individual alerts are not firing.

## Implementation

Forward Kubernetes events via the Splunk connector with the type field preserved. Filter out known noisy reasons with a lookup. Baseline typical Warning vs Error counts per day and alert when Error count exceeds threshold or Warning grows week-over-week. Optionally split by involvedObject.namespace for drilldown.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes.
• Ensure the following data sources are available: `index=containers sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward Kubernetes events via the Splunk connector with the type field preserved. Filter out known noisy reasons with a lookup. Baseline typical Warning vs Error counts per day and alert when Error count exceeds threshold or Warning grows week-over-week. Optionally split by involvedObject.namespace for drilldown.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="kube:events" type IN ("Warning", "Error")
| timechart span=1d count by type
| trendline sma7(Warning) as warning_trend sma7(Error) as error_trend
```

Understanding this SPL

**Kubernetes Event Error Rate Trending** — Warning and error Kubernetes events aggregate noise from image pulls, scheduling failures, and control-plane issues. A rising daily rate of Warning/Error events signals systemic problems even when individual alerts are not firing.

Documented **Data sources**: `index=containers sourcetype=kube:events`. **App/TA** (typical add-on context): Splunk Connect for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: kube:events. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="kube:events". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by type** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Kubernetes Event Error Rate Trending**): trendline sma7(Warning) as warning_trend sma7(Error) as error_trend


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (Warning vs Error per day), line chart overlay with 7-day SMA.

## SPL

```spl
index=containers sourcetype="kube:events" type IN ("Warning", "Error")
| timechart span=1d count by type
| trendline sma7(Warning) as warning_trend sma7(Error) as error_trend
```

## Visualization

Column chart (Warning vs Error per day), line chart overlay with 7-day SMA.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
