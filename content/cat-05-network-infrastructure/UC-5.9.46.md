---
id: "5.9.46"
title: "ThousandEyes Alert Severity Distribution"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.46 · ThousandEyes Alert Severity Distribution

## Description

Provides a centralized view of all ThousandEyes alerts in Splunk by severity, enabling SOC and NOC teams to prioritize response across network, application, and voice test alerts alongside other infrastructure alerts.

## Value

Provides a centralized view of all ThousandEyes alerts in Splunk by severity, enabling SOC and NOC teams to prioritize response across network, application, and voice test alerts alongside other infrastructure alerts.

## Implementation

Configure the Alerts Stream input in the Cisco ThousandEyes App for Splunk. Select the ThousandEyes user, account group, and alert rules to receive. The app automatically creates a webhook connector in ThousandEyes and associates it with selected alert rules. Alerts flow in real-time to Splunk via HEC. The Splunk App Alerts dashboard provides pre-built panels for alert severity distribution, timeline, and drilldown.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure the Alerts Stream input in the Cisco ThousandEyes App for Splunk. Select the ThousandEyes user, account group, and alert rules to receive. The app automatically creates a webhook connector in ThousandEyes and associates it with selected alert rules. Alerts flow in real-time to Splunk via HEC. The Splunk App Alerts dashboard provides pre-built panels for alert severity distribution, timeline, and drilldown.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats count by severity, alert.rule.name, alert.test.name, alert.type
| sort severity, -count
```

Understanding this SPL

**ThousandEyes Alert Severity Distribution** — Provides a centralized view of all ThousandEyes alerts in Splunk by severity, enabling SOC and NOC teams to prioritize response across network, application, and voice test alerts alongside other infrastructure alerts.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **sourcetype**: thousandeyes:alerts. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by severity, alert.rule.name, alert.test.name, alert.type** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (alerts by severity), Bar chart (alerts by type), Table (rule, test, severity, count), Single value (active critical alerts).

## SPL

```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats count by severity, alert.rule.name, alert.test.name, alert.type
| sort severity, -count
```

## Visualization

Pie chart (alerts by severity), Bar chart (alerts by type), Table (rule, test, severity, count), Single value (active critical alerts).

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
