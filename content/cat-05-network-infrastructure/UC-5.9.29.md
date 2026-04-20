---
id: "5.9.29"
title: "SD-WAN Overlay vs Underlay Performance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.29 · SD-WAN Overlay vs Underlay Performance

## Description

Compares performance metrics across SD-WAN overlay tunnels and their underlay transport paths, revealing when SD-WAN policy routing decisions are sub-optimal or when underlay degradation affects the overlay.

## Value

Compares performance metrics across SD-WAN overlay tunnels and their underlay transport paths, revealing when SD-WAN policy routing decisions are sub-optimal or when underlay degradation affects the overlay.

## Implementation

Deploy ThousandEyes Enterprise Agents on Cisco Catalyst SD-WAN or Meraki MX devices via the SD-WAN Manager integration. Create paired tests — one through the overlay tunnel and one via the underlay path — and name them consistently (e.g., "Site-A Overlay", "Site-A Underlay") to enable comparison. The same `network.latency`, `network.loss`, and `network.jitter` metrics apply.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics, Path Visualization.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy ThousandEyes Enterprise Agents on Cisco Catalyst SD-WAN or Meraki MX devices via the SD-WAN Manager integration. Create paired tests — one through the overlay tunnel and one via the underlay path — and name them consistently (e.g., "Site-A Overlay", "Site-A Underlay") to enable comparison. The same `network.latency`, `network.loss`, and `network.jitter` metrics apply.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="agent-to-agent" OR thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SD-WAN*" OR thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, thousandeyes.test.name
```

Understanding this SPL

**SD-WAN Overlay vs Underlay Performance** — Compares performance metrics across SD-WAN overlay tunnels and their underlay transport paths, revealing when SD-WAN policy routing decisions are sub-optimal or when underlay degradation affects the overlay.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics, Path Visualization. **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Dual-panel comparison (overlay vs underlay), Table (test, latency, loss, jitter), Line chart side-by-side.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-agent" OR thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SD-WAN*" OR thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, thousandeyes.test.name
```

## Visualization

Dual-panel comparison (overlay vs underlay), Table (test, latency, loss, jitter), Line chart side-by-side.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
