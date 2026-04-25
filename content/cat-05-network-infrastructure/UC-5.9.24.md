<!-- AUTO-GENERATED from UC-5.9.24.json — DO NOT EDIT -->

---
id: "5.9.24"
title: "Endpoint Experience Score Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.24 · Endpoint Experience Score Monitoring

## Description

ThousandEyes Endpoint Agents provide a composite experience score aggregating CPU, memory, and network performance from the end-user device perspective, enabling proactive digital experience management for hybrid workforces.

## Value

ThousandEyes Endpoint Agents provide a composite experience score aggregating CPU, memory, and network performance from the end-user device perspective, enabling proactive digital experience management for hybrid workforces.

## Implementation

Deploy ThousandEyes Endpoint Agents on user devices and configure Endpoint Agent tests in the Tests Stream input. The OTel metric `thousandeyes.endpoint.agent.score` is a composite of CPU and memory scores. `system.cpu.utilization` and `system.memory.utilization` are reported as percentages.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy ThousandEyes Endpoint Agents on user devices and configure Endpoint Agent tests in the Tests Stream input. The OTel metric `thousandeyes.endpoint.agent.score` is a composite of CPU and memory scores. `system.cpu.utilization` and `system.memory.utilization` are reported as percentages.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(thousandeyes.endpoint.agent.score) as avg_score avg(system.cpu.utilization) as avg_cpu avg(system.memory.utilization) as avg_mem by thousandeyes.source.agent.name
| where avg_score < 70
| sort avg_score
```

Understanding this SPL

**Endpoint Experience Score Monitoring** — ThousandEyes Endpoint Agents provide a composite experience score aggregating CPU, memory, and network performance from the end-user device perspective, enabling proactive digital experience management for hybrid workforces.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_score < 70` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (experience score per user), Table (agent, score, CPU, memory), Trend line chart.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(thousandeyes.endpoint.agent.score) as avg_score avg(system.cpu.utilization) as avg_cpu avg(system.memory.utilization) as avg_mem by thousandeyes.source.agent.name
| where avg_score < 70
| sort avg_score
```

## Visualization

Gauge (experience score per user), Table (agent, score, CPU, memory), Trend line chart.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
