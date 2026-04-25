<!-- AUTO-GENERATED from UC-5.9.34.json — DO NOT EDIT -->

---
id: "5.9.34"
title: "HTTP Server Availability Monitoring (ThousandEyes)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.34 · HTTP Server Availability Monitoring (ThousandEyes)

## Description

Monitors web server availability from multiple global vantage points using ThousandEyes Cloud and Enterprise Agents. Detects regional outages that internal monitoring misses because the problem is between the user and the server.

## Value

Monitors web server availability from multiple global vantage points using ThousandEyes Cloud and Enterprise Agents. Detects regional outages that internal monitoring misses because the problem is between the user and the server.

## Implementation

Create HTTP Server tests in ThousandEyes targeting critical web applications and stream metrics to Splunk via the Tests Stream input. The OTel metric `http.server.request.availability` reports 100% when the HTTP request succeeds and 0% when any error occurs. The Splunk App Application dashboard includes an "HTTP Server Availability (%)" panel with permalink drilldown.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create HTTP Server tests in ThousandEyes targeting critical web applications and stream metrics to Splunk via the Tests Stream input. The OTel metric `http.server.request.availability` reports 100% when the HTTP request succeeds and 0% when any error occurs. The Splunk App Application dashboard includes an "HTTP Server Availability (%)" panel with permalink drilldown.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```

Understanding this SPL

**HTTP Server Availability Monitoring (ThousandEyes)** — Monitors web server availability from multiple global vantage points using ThousandEyes Cloud and Enterprise Agents. Detects regional outages that internal monitoring misses because the problem is between the user and the server.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, server.address, thousandeyes.source.agent.name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_availability < 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (availability % over time), Single value (current availability), Table (test, server, agent, availability).

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```

## Visualization

Line chart (availability % over time), Single value (current availability), Table (test, server, agent, availability).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
