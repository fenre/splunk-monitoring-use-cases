---
id: "7.3.9"
title: "Azure Cosmos DB RU Consumption"
criticality: "high"
splunkPillar: "Observability"
---

# UC-7.3.9 · Azure Cosmos DB RU Consumption

## Description

Normalized RU/s consumption vs provisioned throughput identifies hot partitions and autoscale effectiveness.

## Value

Normalized RU/s consumption vs provisioned throughput identifies hot partitions and autoscale effectiveness.

## Implementation

Map exact metric names from your Azure diagnostic settings. Alert when normalized consumption >90% sustained. Split by partition key if available in custom dimensions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`, Azure Monitor metrics.
• Ensure the following data sources are available: `NormalizedRUConsumption`, `Total Request Units`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map exact metric names from your Azure diagnostic settings. Alert when normalized consumption >90% sustained. Split by partition key if available in custom dimensions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mssql:azuremonitor" OR sourcetype="azure:metrics"
| search metric_name="NormalizedRUConsumption" OR "*Cosmos*"
| timechart span=5m avg(average) as norm_ru by DatabaseName, CollectionName
| where norm_ru > 0.9
```

Understanding this SPL

**Azure Cosmos DB RU Consumption** — Normalized RU/s consumption vs provisioned throughput identifies hot partitions and autoscale effectiveness.

Documented **Data sources**: `NormalizedRUConsumption`, `Total Request Units`. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`, Azure Monitor metrics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mssql:azuremonitor, azure:metrics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mssql:azuremonitor". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by DatabaseName, CollectionName** — ideal for trending and alerting on this use case.
• Filters the current rows with `where norm_ru > 0.9` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (RU consumption %), Table (collections over threshold), Single value (hottest collection).

## SPL

```spl
index=azure sourcetype="mssql:azuremonitor" OR sourcetype="azure:metrics"
| search metric_name="NormalizedRUConsumption" OR "*Cosmos*"
| timechart span=5m avg(average) as norm_ru by DatabaseName, CollectionName
| where norm_ru > 0.9
```

## Visualization

Line chart (RU consumption %), Table (collections over threshold), Single value (hottest collection).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
