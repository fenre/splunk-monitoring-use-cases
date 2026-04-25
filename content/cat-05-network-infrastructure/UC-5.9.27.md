<!-- AUTO-GENERATED from UC-5.9.27.json — DO NOT EDIT -->

---
id: "5.9.27"
title: "Endpoint Connection Type and Network Score"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.27 · Endpoint Connection Type and Network Score

## Description

Comparing network scores across connection types (Wireless, Ethernet, Modem) identifies whether WiFi or wired connectivity is a systemic issue for the workforce, informing infrastructure investment decisions.

## Value

Comparing network scores across connection types (Wireless, Ethernet, Modem) identifies whether WiFi or wired connectivity is a systemic issue for the workforce, informing infrastructure investment decisions.

## Implementation

The OTel attribute `thousandeyes.source.agent.connection.type` reports "Wireless", "Ethernet", or "Modem". Group endpoint network metrics by connection type to identify whether WiFi users have systematically worse performance than wired users.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
The OTel attribute `thousandeyes.source.agent.connection.type` reports "Wireless", "Ethernet", or "Modem". Group endpoint network metrics by connection type to identify whether WiFi users have systematically worse performance than wired users.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss count by thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

Understanding this SPL

**Endpoint Connection Type and Network Score** — Comparing network scores across connection types (Wireless, Ethernet, Modem) identifies whether WiFi or wired connectivity is a systemic issue for the workforce, informing infrastructure investment decisions.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.connection.type** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (score by connection type), Table (connection type, avg score, latency, loss, count), Pie chart (user distribution by type).

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss count by thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

## Visualization

Column chart (score by connection type), Table (connection type, avg score, latency, loss, count), Pie chart (user distribution by type).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
