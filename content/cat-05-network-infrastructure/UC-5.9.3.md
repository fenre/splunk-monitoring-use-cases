<!-- AUTO-GENERATED from UC-5.9.3.json — DO NOT EDIT -->

---
id: "5.9.3"
title: "Network Jitter Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.3 · Network Jitter Monitoring

## Description

Jitter (variation in packet delay) directly affects real-time applications like VoIP and video. High jitter degrades voice quality even when latency is acceptable.

## Value

Jitter (variation in packet delay) directly affects real-time applications like VoIP and video. High jitter degrades voice quality even when latency is acceptable.

## Implementation

The OTel metric `network.jitter` reports the standard deviation of round-trip times in milliseconds. Jitter above 30 ms typically degrades voice quality. Correlate with `network.latency` and `network.loss` for a complete path quality picture.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel metric `network.jitter` reports the standard deviation of round-trip times in milliseconds. Jitter above 30 ms typically degrades voice quality. Correlate with `network.latency` and `network.loss` for a complete path quality picture.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.jitter) as avg_jitter_ms max(network.jitter) as max_jitter_ms by thousandeyes.source.agent.name, server.address
| where avg_jitter_ms > 30
| sort -avg_jitter_ms
```

Understanding this SPL

**Network Jitter Monitoring** — Jitter (variation in packet delay) directly affects real-time applications like VoIP and video. High jitter degrades voice quality even when latency is acceptable.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_jitter_ms > 30` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (jitter ms over time), Combined chart (latency + jitter + loss), Table.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.jitter) as avg_jitter_ms max(network.jitter) as max_jitter_ms by thousandeyes.source.agent.name, server.address
| where avg_jitter_ms > 30
| sort -avg_jitter_ms
```

## Visualization

Line chart (jitter ms over time), Combined chart (latency + jitter + loss), Table.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
