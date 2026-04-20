---
id: "3.6.4"
title: "Resource Request vs Limit Utilization Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.6.4 · Resource Request vs Limit Utilization Trending

## Description

Comparing actual CPU and memory usage to requested and limit values shows whether workloads are over-provisioned, at risk of throttling or OOM, or drifting after code changes. Trending utilization percentages highlights capacity pressure before quotas cause scheduling failures.

## Value

Comparing actual CPU and memory usage to requested and limit values shows whether workloads are over-provisioned, at risk of throttling or OOM, or drifting after code changes. Trending utilization percentages highlights capacity pressure before quotas cause scheduling failures.

## Implementation

Align metric names with your Prometheus/OpenTelemetry pipeline. Ensure pod labels match between usage and request series. Cap percentages at 100% for display where usage can briefly exceed requests. Review namespaces trending above 85% of request or near limit consistently for right-sizing or HPA tuning. Duplicate the panel for memory utilization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: OpenTelemetry Collector, Prometheus-compatible scrape to Splunk.
• Ensure the following data sources are available: `index=containers` via `mstats` — `k8s.pod.cpu.utilization`, `k8s.pod.memory.usage`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Align metric names with your Prometheus/OpenTelemetry pipeline. Ensure pod labels match between usage and request series. Cap percentages at 100% for display where usage can briefly exceed requests. Review namespaces trending above 85% of request or near limit consistently for right-sizing or HPA tuning. Duplicate the panel for memory utilization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats avg(k8s.pod.cpu.utilization) as cpu_util WHERE index=containers by namespace span=1d
| sort namespace, _time
| streamstats window=7 avg(cpu_util) as cpu_trend by namespace
| table _time, namespace, cpu_util, cpu_trend
```

Understanding this SPL

**Resource Request vs Limit Utilization Trending** — Comparing actual CPU and memory usage to requested and limit values shows whether workloads are over-provisioned, at risk of throttling or OOM, or drifting after code changes. Trending utilization percentages highlights capacity pressure before quotas cause scheduling failures.

Documented **Data sources**: `index=containers` via `mstats` — `k8s.pod.cpu.utilization`, `k8s.pod.memory.usage`. **App/TA** (typical add-on context): OpenTelemetry Collector, Prometheus-compatible scrape to Splunk. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `streamstats` rolls up events into metrics; results are split **by namespace** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Resource Request vs Limit Utilization Trending**): table _time, namespace, cpu_util, cpu_trend

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (avg CPU % of request by namespace, 30 days), dual panel for memory, heatmap (namespace x day).

## SPL

```spl
| mstats avg(k8s.pod.cpu.utilization) as cpu_util WHERE index=containers by namespace span=1d
| sort namespace, _time
| streamstats window=7 avg(cpu_util) as cpu_trend by namespace
| table _time, namespace, cpu_util, cpu_trend
```

## Visualization

Line chart (avg CPU % of request by namespace, 30 days), dual panel for memory, heatmap (namespace x day).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
