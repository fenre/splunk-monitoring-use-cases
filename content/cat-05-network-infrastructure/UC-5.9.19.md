<!-- AUTO-GENERATED from UC-5.9.19.json — DO NOT EDIT -->

---
id: "5.9.19"
title: "ISP Performance Degradation Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.9.19 · ISP Performance Degradation Alerts

## Description

ThousandEyes alerts notify when ISP-level degradation is detected. Ingesting these alerts into Splunk provides a centralized view alongside other infrastructure alerts and enables correlation with internal incidents.

## Value

ThousandEyes alerts notify when ISP-level degradation is detected. Ingesting these alerts into Splunk provides a centralized view alongside other infrastructure alerts and enables correlation with internal incidents.

## Implementation

Configure the Alerts Stream input in the ThousandEyes App, selecting alert rules to receive via webhook. The app automatically creates a webhook connector in ThousandEyes and associates it with the selected alert rules. Alerts flow in real-time to Splunk via HEC.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure the Alerts Stream input in the ThousandEyes App, selecting alert rules to receive via webhook. The app automatically creates a webhook connector in ThousandEyes and associates it with the selected alert rules. Alerts flow in real-time to Splunk via HEC.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` sourcetype="thousandeyes:alerts" severity="critical" OR severity="warning"
| stats count by alert.rule.name, alert.test.name, severity
| sort -count
```

Understanding this SPL

**ISP Performance Degradation Alerts** — ThousandEyes alerts notify when ISP-level degradation is detected. Ingesting these alerts into Splunk provides a centralized view alongside other infrastructure alerts and enables correlation with internal incidents.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: thousandeyes:alerts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by alert.rule.name, alert.test.name, severity** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (alerts by severity), Bar chart (alert timeline), Table (rule, test, severity, count).

## SPL

```spl
`stream_index` sourcetype="thousandeyes:alerts" severity="critical" OR severity="warning"
| stats count by alert.rule.name, alert.test.name, severity
| sort -count
```

## Visualization

Pie chart (alerts by severity), Bar chart (alert timeline), Table (rule, test, severity, count).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
