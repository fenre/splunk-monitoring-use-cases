---
id: "4.2.50"
title: "Azure Data Factory Pipeline Failures"
criticality: "high"
splunkPillar: "Observability"
---

# UC-4.2.50 · Azure Data Factory Pipeline Failures

## Description

Data Factory orchestrates ETL/ELT pipelines that feed data warehouses, analytics, and operational systems. Pipeline failures cause stale data, broken dashboards, and missed SLAs.

## Value

Data Factory orchestrates ETL/ELT pipelines that feed data warehouses, analytics, and operational systems. Pipeline failures cause stale data, broken dashboards, and missed SLAs.

## Implementation

Enable diagnostics on Data Factory to route `PipelineRuns`, `ActivityRuns`, and `TriggerRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause (copy failures, data flow errors, linked service timeouts). Monitor pipeline duration trending to detect degradation before SLA breach.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics).
• Ensure the following data sources are available: `sourcetype=azure:diagnostics` (PipelineRuns, ActivityRuns, TriggerRuns).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable diagnostics on Data Factory to route `PipelineRuns`, `ActivityRuns`, and `TriggerRuns` to Splunk via Event Hub. Alert on failed pipeline runs. Track activity-level errors for root cause (copy failures, data flow errors, linked service timeouts). Monitor pipeline duration trending to detect degradation before SLA breach.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cloud sourcetype="azure:diagnostics" Category="PipelineRuns"
| where status="Failed"
| stats count as failures, latest(start) as last_failure by pipelineName, resource_name
| sort -failures
```

Understanding this SPL

**Azure Data Factory Pipeline Failures** — Data Factory orchestrates ETL/ELT pipelines that feed data warehouses, analytics, and operational systems. Pipeline failures cause stale data, broken dashboards, and missed SLAs.

Documented **Data sources**: `sourcetype=azure:diagnostics` (PipelineRuns, ActivityRuns, TriggerRuns). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices` (Azure Monitor diagnostics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cloud; **sourcetype**: azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cloud, sourcetype="azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status="Failed"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by pipelineName, resource_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (failed pipelines with error), Bar chart (failures by pipeline), Line chart (pipeline duration trend).

## SPL

```spl
index=cloud sourcetype="azure:diagnostics" Category="PipelineRuns"
| where status="Failed"
| stats count as failures, latest(start) as last_failure by pipelineName, resource_name
| sort -failures
```

## Visualization

Table (failed pipelines with error), Bar chart (failures by pipeline), Line chart (pipeline duration trend).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
