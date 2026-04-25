<!-- AUTO-GENERATED from UC-4.2.12.json — DO NOT EDIT -->

---
id: "4.2.12"
title: "Cost Management Alerts"
criticality: "low"
splunkPillar: "Observability"
---

# UC-4.2.12 · Cost Management Alerts

## Description

Azure cost monitoring prevents budget overruns. Tracking spend by resource group/team enables chargeback and anomaly detection.

## Value

Azure cost monitoring prevents budget overruns. Tracking spend by resource group/team enables chargeback and anomaly detection.

## Implementation

Configure Azure Cost Management to export daily usage data to a storage account. Ingest in Splunk. Create budget alerts when spending approaches thresholds.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Azure Cost Management export.
• Ensure the following data sources are available: Azure Cost Management data (exported to storage).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Azure Cost Management to export daily usage data to a storage account. Ingest in Splunk. Create budget alerts when spending approaches thresholds.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="azure:costmanagement"
| timechart span=1d sum(CostInBillingCurrency) as daily_cost by ResourceGroup
| eventstats avg(daily_cost) as avg_cost by ResourceGroup
| where daily_cost > avg_cost * 1.5
```

Understanding this SPL

**Cost Management Alerts** — Azure cost monitoring prevents budget overruns. Tracking spend by resource group/team enables chargeback and anomaly detection.

Documented **Data sources**: Azure Cost Management data (exported to storage). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Azure Cost Management export. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: azure:costmanagement. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="azure:costmanagement". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by ResourceGroup** — ideal for trending and alerting on this use case.
• `eventstats` rolls up events into metrics; results are split **by ResourceGroup** so each row reflects one combination of those dimensions.
• Filters the current rows with `where daily_cost > avg_cost * 1.5` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area chart (spend by RG), Line chart with budget overlay, Table.

## SPL

```spl
index=azure sourcetype="azure:costmanagement"
| timechart span=1d sum(CostInBillingCurrency) as daily_cost by ResourceGroup
| eventstats avg(daily_cost) as avg_cost by ResourceGroup
| where daily_cost > avg_cost * 1.5
```

## Visualization

Stacked area chart (spend by RG), Line chart with budget overlay, Table.

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
