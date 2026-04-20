---
id: "4.2.24"
title: "Azure Monitor Alert State Changes"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-4.2.24 · Azure Monitor Alert State Changes

## Description

Alert state changes (fired, resolved) provide consolidated view of metric/log conditions. Centralizing in Splunk enables correlation.

## Value

Alert state changes (fired, resolved) provide consolidated view of metric/log conditions. Centralizing in Splunk enables correlation.

## Implementation

Configure Action Group to send alert payload to Splunk (Logic App or webhook). Ingest fired and resolved events. Dashboard active alerts by severity and resource group.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Activity Log (Microsoft.Insights/activityLogAlerts), or Action Group webhook to Splunk.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Action Group to send alert payload to Splunk (Logic App or webhook). Ingest fired and resolved events. Dashboard active alerts by severity and resource group.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="Microsoft.Insights/activityLogAlerts/Activated/Action"
| table _time caller properties.condition properties.alertRule
| sort -_time
```

Understanding this SPL

**Azure Monitor Alert State Changes** — Alert state changes (fired, resolved) provide consolidated view of metric/log conditions. Centralizing in Splunk enables correlation.

Documented **Data sources**: Activity Log (Microsoft.Insights/activityLogAlerts), or Action Group webhook to Splunk. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:audit. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Azure Monitor Alert State Changes**): table _time caller properties.condition properties.alertRule
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (alert, state, time), Timeline (alert history), Single value (active alerts).

## SPL

```spl
index=azure sourcetype="mscs:azure:audit" operationName.value="Microsoft.Insights/activityLogAlerts/Activated/Action"
| table _time caller properties.condition properties.alertRule
| sort -_time
```

## Visualization

Table (alert, state, time), Timeline (alert history), Single value (active alerts).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
