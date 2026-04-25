<!-- AUTO-GENERATED from UC-5.9.26.json — DO NOT EDIT -->

---
id: "5.9.26"
title: "VPN Path Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.26 · VPN Path Performance

## Description

Measures latency, loss, and quality through VPN tunnels from endpoint agents, identifying whether the VPN concentrator or provider is the bottleneck for remote workers.

## Value

Measures latency, loss, and quality through VPN tunnels from endpoint agents, identifying whether the VPN concentrator or provider is the bottleneck for remote workers.

## Implementation

Endpoint agents with VPN connections report metrics with `target.type="vpn"`. The `vpn.vendor` attribute identifies the VPN client (e.g., "Cisco AnyConnect"). The `server.address` is the VPN gateway. Compare VPN segment scores with gateway and DNS segment scores to isolate whether the VPN is the bottleneck.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Endpoint agents with VPN connections report metrics with `target.type="vpn"`. The `vpn.vendor` attribute identifies the VPN client (e.g., "Cisco AnyConnect"). The `server.address` is the VPN gateway. Compare VPN segment scores with gateway and DNS segment scores to isolate whether the VPN is the bottleneck.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, vpn.vendor, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_score < 70 OR avg_loss > 1
| sort avg_score
```

Understanding this SPL

**VPN Path Performance** — Measures latency, loss, and quality through VPN tunnels from endpoint agents, identifying whether the VPN concentrator or provider is the bottleneck for remote workers.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, vpn.vendor, server.address** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_score < 70 OR avg_loss > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (agent, VPN vendor, gateway, latency, loss, score), Column chart by VPN vendor, Trend line chart.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, vpn.vendor, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_score < 70 OR avg_loss > 1
| sort avg_score
```

## Visualization

Table (agent, VPN vendor, gateway, latency, loss, score), Column chart by VPN vendor, Trend line chart.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
