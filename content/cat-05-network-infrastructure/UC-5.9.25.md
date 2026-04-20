---
id: "5.9.25"
title: "Remote Worker Connectivity Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.25 · Remote Worker Connectivity Health

## Description

Endpoint agents break connectivity into segments (gateway, VPN, proxy, DNS) with per-segment latency, loss, and score, enabling targeted troubleshooting of remote worker network issues without requiring on-site visits.

## Value

Endpoint agents break connectivity into segments (gateway, VPN, proxy, DNS) with per-segment latency, loss, and score, enabling targeted troubleshooting of remote worker network issues without requiring on-site visits.

## Implementation

Endpoint Experience Local Network data reports metrics per segment: `target.type` can be "dns", "proxy", "gateway", or "vpn". The `network.score` composite metric simplifies multi-segment health assessment. Identify whether connectivity problems are in the local network, VPN, proxy, or DNS layer.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Endpoint Experience Local Network data reports metrics per segment: `target.type` can be "dns", "proxy", "gateway", or "vpn". The `network.score` composite metric simplifies multi-segment health assessment. Identify whether connectivity problems are in the local network, VPN, proxy, or DNS layer.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type=*
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, target.type
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, target.type
```

Understanding this SPL

**Remote Worker Connectivity Health** — Endpoint agents break connectivity into segments (gateway, VPN, proxy, DNS) with per-segment latency, loss, and score, enabling targeted troubleshooting of remote worker network issues without requiring on-site visits.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.name, target.type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (agent, segment type, latency, loss, score), Heatmap by segment, Drilldown per agent.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type=*
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, target.type
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, target.type
```

## Visualization

Table (agent, segment type, latency, loss, score), Heatmap by segment, Drilldown per agent.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
