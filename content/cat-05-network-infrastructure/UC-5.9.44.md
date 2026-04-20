---
id: "5.9.44"
title: "Multi-Region SaaS Availability (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.44 · Multi-Region SaaS Availability (ThousandEyes)

## Description

Monitors SaaS application reachability from multiple geographic regions using ThousandEyes Cloud Agents, identifying regional availability issues that affect specific user populations.

## Value

Monitors SaaS application reachability from multiple geographic regions using ThousandEyes Cloud Agents, identifying regional availability issues that affect specific user populations.

## Implementation

Deploy the same HTTP Server tests across ThousandEyes Cloud Agents in Americas, EMEA, and APAC regions. Use `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.location` attributes to group results by region. A service that is available from US agents but not from EU agents indicates a regional issue.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy the same HTTP Server tests across ThousandEyes Cloud Agents in Americas, EMEA, and APAC regions. Use `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.location` attributes to group results by region. A service that is available from US agents but not from EU agents indicates a regional issue.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.location
| where avg_availability < 100
| sort avg_availability
```

Understanding this SPL

**Multi-Region SaaS Availability (ThousandEyes)** — Monitors SaaS application reachability from multiple geographic regions using ThousandEyes Cloud Agents, identifying regional availability issues that affect specific user populations.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.location** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_availability < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (availability by agent location), Table (region, app, availability), Column chart (availability by region).

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.location
| where avg_availability < 100
| sort avg_availability
```

## Visualization

Map (availability by agent location), Table (region, app, availability), Column chart (availability by region).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
