<!-- AUTO-GENERATED from UC-5.9.36.json — DO NOT EDIT -->

---
id: "5.9.36"
title: "HTTP Server Throughput Analysis (ThousandEyes)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.36 · HTTP Server Throughput Analysis (ThousandEyes)

## Description

Measures download throughput from ThousandEyes agents to web servers, revealing bandwidth constraints or content delivery issues from the user perspective.

## Value

Measures download throughput from ThousandEyes agents to web servers, revealing bandwidth constraints or content delivery issues from the user perspective.

## Implementation

The OTel metric `http.server.throughput` reports bytes per second. The Splunk App Application dashboard includes an "HTTP Server Throughput (MB/s)" line chart. Low throughput combined with high latency typically indicates a network bottleneck; low throughput with low latency suggests a server-side rate limit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `http.server.throughput` reports bytes per second. The Splunk App Application dashboard includes an "HTTP Server Throughput (MB/s)" line chart. Low throughput combined with high latency typically indicates a network bottleneck; low throughput with low latency suggests a server-side rate limit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name
| eval throughput_mbps=round(avg_throughput/1048576,2)
| sort -throughput_mbps
```

Understanding this SPL

**HTTP Server Throughput Analysis (ThousandEyes)** — Measures download throughput from ThousandEyes agents to web servers, revealing bandwidth constraints or content delivery issues from the user perspective.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **throughput_mbps** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (throughput MB/s over time), Table (test, agent, throughput), Column chart by agent.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name
| eval throughput_mbps=round(avg_throughput/1048576,2)
| sort -throughput_mbps
```

## Visualization

Line chart (throughput MB/s over time), Table (test, agent, throughput), Column chart by agent.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
