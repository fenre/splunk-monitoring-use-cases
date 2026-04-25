<!-- AUTO-GENERATED from UC-5.9.28.json — DO NOT EDIT -->

---
id: "5.9.28"
title: "Geographic Workforce Performance Comparison"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.28 · Geographic Workforce Performance Comparison

## Description

Comparing digital experience metrics across office locations and regions identifies sites with persistent network quality issues, enabling targeted infrastructure improvements.

## Value

Comparing digital experience metrics across office locations and regions identifies sites with persistent network quality issues, enabling targeted infrastructure improvements.

## Implementation

Endpoint agent metrics include geographic attributes: `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.geo.region.iso_code`. Aggregate network quality metrics by region to identify poorly performing locations. Combine with `thousandeyes.source.agent.location` for more specific site-level analysis.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Endpoint agent metrics include geographic attributes: `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.geo.region.iso_code`. Aggregate network quality metrics by region to identify poorly performing locations. Combine with `thousandeyes.source.agent.location` for more specific site-level analysis.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score count as agent_count by thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.geo.region.iso_code
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort avg_score
```

Understanding this SPL

**Geographic Workforce Performance Comparison** — Comparing digital experience metrics across office locations and regions identifies sites with persistent network quality issues, enabling targeted infrastructure improvements.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.geo.region.iso_code** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_latency_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (score by region), Table (region, score, latency, loss, agent count), Column chart comparing regions.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score count as agent_count by thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.geo.region.iso_code
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort avg_score
```

## Visualization

Map (score by region), Table (region, score, latency, loss, agent count), Column chart comparing regions.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
