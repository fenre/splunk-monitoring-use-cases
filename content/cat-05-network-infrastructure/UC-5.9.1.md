---
id: "5.9.1"
title: "Network Latency Monitoring (Agent-to-Server)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.1 · Network Latency Monitoring (Agent-to-Server)

## Description

Tracks round-trip latency from ThousandEyes agents to target servers, revealing network path degradation before users report slowness.

## Value

Tracks round-trip latency from ThousandEyes agents to target servers, revealing network path degradation before users report slowness.

## Implementation

Install the Cisco ThousandEyes App for Splunk and configure the Tests Stream — Metrics input with HEC. Select the Agent-to-Server tests to stream. Update the `stream_index` macro to point to the correct index. The OTel metric `network.latency` reports maximum round-trip time in seconds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install the Cisco ThousandEyes App for Splunk and configure the Tests Stream — Metrics input with HEC. Select the Agent-to-Server tests to stream. Update the `stream_index` macro to point to the correct index. The OTel metric `network.latency` reports maximum round-trip time in seconds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency_s max(network.latency) as max_latency_s by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1), max_latency_ms=round(max_latency_s*1000,1)
| where avg_latency_ms > 100
| sort -avg_latency_ms
```

Understanding this SPL

**Network Latency Monitoring (Agent-to-Server)** — Tracks round-trip latency from ThousandEyes agents to target servers, revealing network path degradation before users report slowness.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, server.address** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_latency_ms > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (latency per agent over time), Single value (avg latency), Table (agent, server, latency).

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency_s max(network.latency) as max_latency_s by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1), max_latency_ms=round(max_latency_s*1000,1)
| where avg_latency_ms > 100
| sort -avg_latency_ms
```

## Visualization

Line chart (latency per agent over time), Single value (avg latency), Table (agent, server, latency).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
