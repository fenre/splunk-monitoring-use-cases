---
id: "5.9.4"
title: "Agent-to-Agent Latency and Throughput"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.4 · Agent-to-Agent Latency and Throughput

## Description

Measures bidirectional network performance between two ThousandEyes agents, useful for assessing site-to-site WAN link quality and SD-WAN overlay performance.

## Value

Measures bidirectional network performance between two ThousandEyes agents, useful for assessing site-to-site WAN link quality and SD-WAN overlay performance.

## Implementation

Create Agent-to-Agent tests in ThousandEyes between sites and stream metrics. The `network.io.direction` attribute distinguishes `transmit`, `receive`, and `round-trip` measurements. Compare forward and reverse paths to identify asymmetric routing issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create Agent-to-Agent tests in ThousandEyes between sites and stream metrics. The `network.io.direction` attribute distinguishes `transmit`, `receive`, and `round-trip` measurements. Compare forward and reverse paths to identify asymmetric routing issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter_ms by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, network.io.direction
```

Understanding this SPL

**Agent-to-Agent Latency and Throughput** — Measures bidirectional network performance between two ThousandEyes agents, useful for assessing site-to-site WAN link quality and SD-WAN overlay performance.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source agent, target agent, direction, latency, loss, jitter), Line chart per direction.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter_ms by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, network.io.direction
```

## Visualization

Table (source agent, target agent, direction, latency, loss, jitter), Line chart per direction.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
