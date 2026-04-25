<!-- AUTO-GENERATED from UC-5.9.53.json — DO NOT EDIT -->

---
id: "5.9.53"
title: "Cross-Platform Correlation (ThousandEyes Network + Splunk APM)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.53 · Cross-Platform Correlation (ThousandEyes Network + Splunk APM)

## Description

Correlates ThousandEyes network path quality data with Splunk APM application traces to determine whether performance issues are caused by the network or the application. This is the core value proposition of the Splunk + ThousandEyes integration — unified observability across network and application layers.

## Value

Correlates ThousandEyes network path quality data with Splunk APM application traces to determine whether performance issues are caused by the network or the application. This is the core value proposition of the Splunk + ThousandEyes integration — unified observability across network and application layers.

## Implementation

This correlation requires both ThousandEyes network data and Splunk APM trace data indexed in Splunk. The key join field is the server address or service endpoint. When network latency is high but application processing is fast, the network is the bottleneck. When network latency is low but application response is slow, the issue is in the application. This "network vs. app" isolation significantly reduces MTTR by directing the right team to investigate.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), Splunk APM.
• Ensure the following data sources are available: `index=thousandeyes` (network metrics), Splunk APM traces.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
This correlation requires both ThousandEyes network data and Splunk APM trace data indexed in Splunk. The key join field is the server address or service endpoint. When network latency is high but application processing is fast, the network is the bottleneck. When network latency is low but application response is slow, the issue is in the application. This "network vs. app" isolation significantly reduces MTTR by directing the right team to investigate.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| bin _time span=5m
| stats avg(network.latency) as avg_net_latency_s avg(network.loss) as avg_net_loss by server.address, _time
| join type=outer max=1 server.address [
  search index=apm_traces
  | bin _time span=5m
| stats avg(duration_ms) as avg_app_latency_ms p99(duration_ms) as p99_app_latency_ms by service.name, server.address, _time
]
| eval avg_net_latency_ms=round(avg_net_latency_s*1000,1)
| eval root_cause=case(avg_net_latency_ms>200 AND avg_app_latency_ms<500, "Network", avg_net_latency_ms<50 AND avg_app_latency_ms>2000, "Application", avg_net_latency_ms>200 AND avg_app_latency_ms>2000, "Both", 1=1, "Normal")
| where root_cause!="Normal"
| table _time, server.address, service.name, avg_net_latency_ms, avg_net_loss, avg_app_latency_ms, root_cause
```

Understanding this SPL

**Cross-Platform Correlation (ThousandEyes Network + Splunk APM)** — Correlates ThousandEyes network path quality data with Splunk APM application traces to determine whether performance issues are caused by the network or the application. This is the core value proposition of the Splunk + ThousandEyes integration — unified observability across network and application layers.

Documented **Data sources**: `index=thousandeyes` (network metrics), Splunk APM traces. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), Splunk APM. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by server.address, _time** so each row reflects one combination of those dimensions.
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• `eval` defines or adjusts **avg_net_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **root_cause** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where root_cause!="Normal"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Cross-Platform Correlation (ThousandEyes Network + Splunk APM)**): table _time, server.address, service.name, avg_net_latency_ms, avg_net_loss, avg_app_latency_ms, root_cause


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (endpoint, network latency, app latency, root cause), Dual-axis chart (network vs app latency), Dashboard with network and app panels side-by-side.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| bin _time span=5m
| stats avg(network.latency) as avg_net_latency_s avg(network.loss) as avg_net_loss by server.address, _time
| join type=outer max=1 server.address [
  search index=apm_traces
  | bin _time span=5m
| stats avg(duration_ms) as avg_app_latency_ms p99(duration_ms) as p99_app_latency_ms by service.name, server.address, _time
]
| eval avg_net_latency_ms=round(avg_net_latency_s*1000,1)
| eval root_cause=case(avg_net_latency_ms>200 AND avg_app_latency_ms<500, "Network", avg_net_latency_ms<50 AND avg_app_latency_ms>2000, "Application", avg_net_latency_ms>200 AND avg_app_latency_ms>2000, "Both", 1=1, "Normal")
| where root_cause!="Normal"
| table _time, server.address, service.name, avg_net_latency_ms, avg_net_loss, avg_app_latency_ms, root_cause
```

## Visualization

Table (endpoint, network latency, app latency, root cause), Dual-axis chart (network vs app latency), Dashboard with network and app panels side-by-side.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
