---
id: "3.6.1"
title: "Pod Restart Rate Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.1 · Pod Restart Rate Trending

## Description

A rising cluster-wide pod restart rate points to unstable workloads, resource pressure, or bad rollouts before a single namespace triggers a critical alert. Trending over 30 days reveals whether reliability is improving or degrading after platform changes.

## Value

A rising cluster-wide pod restart rate points to unstable workloads, resource pressure, or bad rollouts before a single namespace triggers a critical alert. Trending over 30 days reveals whether reliability is improving or degrading after platform changes.

## Implementation

Ensure kube-state-metrics or the OpenTelemetry Kubernetes receiver emits container restart counters into Splunk metrics. Run the panel on a 30-day window and baseline normal daily restarts per cluster. Alert when the 7-day moving average exceeds the prior 30-day baseline by more than 50%. Exclude system namespaces (kube-system, monitoring) if they skew the signal.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Connect for Kubernetes, OpenTelemetry Collector for Kubernetes.
• Ensure the following data sources are available: `index=containers` metrics via `mstats` (`kube_pod_container_status_restarts_total`), or `sourcetype=kube:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ensure kube-state-metrics or the OpenTelemetry Kubernetes receiver emits container restart counters into Splunk metrics. Run the panel on a 30-day window and baseline normal daily restarts per cluster. Alert when the 7-day moving average exceeds the prior 30-day baseline by more than 50%. Exclude system namespaces (kube-system, monitoring) if they skew the signal.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats latest(kube_pod_container_status_restarts_total) as restarts WHERE index=containers by namespace span=1d
| timechart span=1d sum(restarts) as total_restarts
| trendline sma7(total_restarts) as restart_trend
```

Understanding this SPL

**Pod Restart Rate Trending** — A rising cluster-wide pod restart rate points to unstable workloads, resource pressure, or bad rollouts before a single namespace triggers a critical alert. Trending over 30 days reveals whether reliability is improving or degrading after platform changes.

Documented **Data sources**: `index=containers` metrics via `mstats` (`kube_pod_container_status_restarts_total`), or `sourcetype=kube:events`. **App/TA** (typical add-on context): Splunk Connect for Kubernetes, OpenTelemetry Collector for Kubernetes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `timechart` plots the metric over time using **span=1d** buckets — ideal for trending and alerting on this use case.
• Pipeline stage (see **Pod Restart Rate Trending**): trendline sma7(total_restarts) as restart_trend

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (daily restarts with 7-day SMA, 30 days), area chart by namespace.

## SPL

```spl
| mstats latest(kube_pod_container_status_restarts_total) as restarts WHERE index=containers by namespace span=1d
| timechart span=1d sum(restarts) as total_restarts
| trendline sma7(total_restarts) as restart_trend
```

## Visualization

Line chart (daily restarts with 7-day SMA, 30 days), area chart by namespace.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
