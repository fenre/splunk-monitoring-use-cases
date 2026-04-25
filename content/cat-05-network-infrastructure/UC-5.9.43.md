<!-- AUTO-GENERATED from UC-5.9.43.json — DO NOT EDIT -->

---
id: "5.9.43"
title: "SaaS Application Response Time Comparison (ThousandEyes)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.43 · SaaS Application Response Time Comparison (ThousandEyes)

## Description

Compares availability and response time across business-critical SaaS applications (Microsoft 365, Salesforce, ServiceNow, etc.) from multiple office locations, enabling data-driven SaaS vendor performance management.

## Value

Compares availability and response time across business-critical SaaS applications (Microsoft 365, Salesforce, ServiceNow, etc.) from multiple office locations, enabling data-driven SaaS vendor performance management.

## Implementation

Create HTTP Server or Page Load tests in ThousandEyes for each SaaS application, running from Enterprise Agents at each office and Cloud Agents in relevant regions. Name tests consistently (e.g., "M365 - Exchange Online", "Salesforce - Login Page"). ThousandEyes provides best-practice monitoring guides for Microsoft 365, Salesforce, and other major SaaS platforms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server / Page Load tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create HTTP Server or Page Load tests in ThousandEyes for each SaaS application, running from Enterprise Agents at each office and Cloud Agents in relevant regions. Name tests consistently (e.g., "M365 - Exchange Online", "Salesforce - Login Page"). ThousandEyes provides best-practice monitoring guides for Microsoft 365, Salesforce, and other major SaaS platforms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server" OR thousandeyes.test.type="page-load"
| search thousandeyes.test.name="*M365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*"
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
| sort thousandeyes.test.name, avg_ttfb_ms
```

Understanding this SPL

**SaaS Application Response Time Comparison (ThousandEyes)** — Compares availability and response time across business-critical SaaS applications (Microsoft 365, Salesforce, ServiceNow, etc.) from multiple office locations, enabling data-driven SaaS vendor performance management.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server / Page Load tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, thousandeyes.source.agent.location** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_ttfb_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Column chart (TTFB by SaaS app per location), Table (app, location, availability, TTFB), Comparison dashboard.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server" OR thousandeyes.test.type="page-load"
| search thousandeyes.test.name="*M365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*"
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
| sort thousandeyes.test.name, avg_ttfb_ms
```

## Visualization

Column chart (TTFB by SaaS app per location), Table (app, location, availability, TTFB), Comparison dashboard.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
